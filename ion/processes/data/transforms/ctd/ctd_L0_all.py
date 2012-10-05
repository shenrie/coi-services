'''
@author MManning
@file ion/processes/data/transforms/ctd/ctd_L0_all.py
@description Transforms CTD parsed data into L0 streams
'''

from pyon.ion.transforma import TransformDataProcess, TransformAlgorithm
from pyon.service.service import BaseService
from pyon.core.exception import BadRequest
from pyon.public import IonObject, RT, log
from pyon.util.arg_check import validate_true
from coverage_model.parameter import ParameterDictionary, ParameterContext
from coverage_model.parameter_types import QuantityType
from coverage_model.basic_types import AxisTypeEnum
from pyon.net.endpoint import Publisher
import numpy as np
from pyon.core.bootstrap import get_sys_name
from pyon.net.transport import NameTrio
import re

### For new granule and stream interface
from ion.services.dm.utility.granule.record_dictionary import RecordDictionaryTool
from ion.core.function.transform_function import MultiGranuleTransformFunction

# For usage: please refer to the integration tests in
# ion/processes/data/transforms/ctd/test/test_ctd_transforms.py

class ctd_L0_all(TransformDataProcess):
    """Model for a TransformDataProcess

    """
    def on_start(self):
        super(ctd_L0_all, self).on_start()
        config_streams = self.CFG.process.publish_streams
        requirement = config_streams.has_key('conductivity') \
                        and config_streams.has_key('pressure') \
                        and config_streams.has_key('temperature')

        if not requirement:
            raise AssertionError("For CTD transforms, please send the stream_ids for conductivity, temperature, pressure"
                                 " using special keywords (ex: conductivity) for each instead of just \'output \'")

    def recv_packet(self, packet,stream_route, stream_id):
        """Processes incoming data!!!!
            @param packet granule
            @param stream_route StreamRoute
            @param stream_id str
        """
        if packet == {}:
            return
        granules = ctd_L0_algorithm.execute([packet])
        for granule in granules:
            self.conductivity.publish(msg = granule['conductivity'])
            self.temperature.publish(msg = granule['temp'])
            self.pressure.publish(msg = granule['pressure'])

class ctd_L0_algorithm(MultiGranuleTransformFunction):

    @staticmethod
    @MultiGranuleTransformFunction.validate_inputs
    def execute(input=None, context=None, config=None, params=None, state=None):
        '''
        @param input granule
        @retval result_list list of dictionaries containing granules as values
        '''

        result_list = []
        for x in input:
            rdt = RecordDictionaryTool.load_from_granule(x)

            conductivity = rdt['conductivity']
            pressure = rdt['pressure']
            temperature = rdt['temp']

            longitude = rdt['lon']
            latitude = rdt['lat']
            time = rdt['time']
            depth = rdt['depth']

            result = {}

            # create parameter settings
            cond_pdict = ctd_L0_algorithm._create_parameter("conductivity")
            pres_pdict = ctd_L0_algorithm._create_parameter("pressure")
            temp_pdict = ctd_L0_algorithm._create_parameter("temp")

            # build the granules for conductivity, temperature and pressure
            result['conductivity'] = ctd_L0_algorithm._build_granule_settings(cond_pdict, 'conductivity', conductivity, time, latitude, longitude, depth)
            result['temp'] = ctd_L0_algorithm._build_granule_settings(temp_pdict, 'temp', temperature, time, latitude, longitude, depth)
            result['pressure'] = ctd_L0_algorithm._build_granule_settings(pres_pdict, 'pressure', pressure, time, latitude, longitude, depth)

            result_list.append(result)

        return result_list

    @staticmethod
    def _create_parameter(name):
        '''
        @param name str
        @retval pdict ParameterDictionary
        '''

        pdict = ParameterDictionary()

        pdict = ctd_L0_algorithm._add_location_time_ctxt(pdict)

        if name == 'conductivity':
            cond_ctxt = ParameterContext('conductivity', param_type=QuantityType(value_encoding=np.float32))
            cond_ctxt.uom = 'unknown'
            cond_ctxt.fill_value = 0e0
            pdict.add_context(cond_ctxt)

        elif name == "pressure":
            pres_ctxt = ParameterContext('pressure', param_type=QuantityType(value_encoding=np.float32))
            pres_ctxt.uom = 'Pascal'
            pres_ctxt.fill_value = 0x0
            pdict.add_context(pres_ctxt)

        elif name == "temp":
            temp_ctxt = ParameterContext('temp', param_type=QuantityType(value_encoding=np.float32))
            temp_ctxt.uom = 'degree_Celsius'
            temp_ctxt.fill_value = 0e0
            pdict.add_context(temp_ctxt)

        return pdict

    @staticmethod
    def _add_location_time_ctxt(pdict):
        '''
        @param pdict ParameterDictionary
        @retval pdict ParameterDictionary
        '''

        t_ctxt = ParameterContext('time', param_type=QuantityType(value_encoding=np.int64))
        t_ctxt.reference_frame = AxisTypeEnum.TIME
        t_ctxt.uom = 'seconds since 1970-01-01'
        t_ctxt.fill_value = 0x0
        pdict.add_context(t_ctxt)

        lat_ctxt = ParameterContext('lat', param_type=QuantityType(value_encoding=np.float32))
        lat_ctxt.reference_frame = AxisTypeEnum.LAT
        lat_ctxt.uom = 'degree_north'
        lat_ctxt.fill_value = 0e0
        pdict.add_context(lat_ctxt)

        lon_ctxt = ParameterContext('lon', param_type=QuantityType(value_encoding=np.float32))
        lon_ctxt.reference_frame = AxisTypeEnum.LON
        lon_ctxt.uom = 'degree_east'
        lon_ctxt.fill_value = 0e0
        pdict.add_context(lon_ctxt)

        depth_ctxt = ParameterContext('depth', param_type=QuantityType(value_encoding=np.float32))
        depth_ctxt.reference_frame = AxisTypeEnum.HEIGHT
        depth_ctxt.uom = 'meters'
        depth_ctxt.fill_value = 0e0
        pdict.add_context(depth_ctxt)

        return pdict

    @staticmethod
    def _build_granule_settings(param_dictionary=None, field_name='', value=None, time=None, latitude=None, longitude=None, depth=None):
        '''
        @param param_dictionary ParameterDictionary
        @param field_name str
        @param value numpy.array
        @param time numpy.array
        @param latitude numpy.array
        @param longitude numpy.array
        @param depth numpy.array

        @retval Granule
        '''
        root_rdt = RecordDictionaryTool(param_dictionary=param_dictionary)

        root_rdt[field_name] = value

        if not time is None:
            root_rdt['time'] = time
        if not latitude is None:
            root_rdt['lat'] = latitude
        if not longitude is None:
            root_rdt['lon'] = longitude
        if not depth is None:
            root_rdt['depth'] = depth

        log.debug("ctd_L0_all:_build_granule_settings: logging published Record Dictionary:\n %s", str(root_rdt.pretty_print()))

        return root_rdt.to_granule()

