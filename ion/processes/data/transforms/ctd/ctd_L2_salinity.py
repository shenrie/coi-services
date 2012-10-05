
'''
@author MManning
@file ion/processes/data/transforms/ctd/ctd_L2_salinity.py
@description Transforms CTD parsed data into L2 product for salinity
'''

from pyon.ion.transforma import TransformDataProcess
from pyon.public import log
import numpy as np

### For new granule and stream interface
from ion.services.dm.utility.granule.record_dictionary import RecordDictionaryTool
from ion.core.function.transform_function import SimpleGranuleTransformFunction
from coverage_model.parameter import ParameterDictionary, ParameterContext
from coverage_model.parameter_types import QuantityType
from coverage_model.basic_types import AxisTypeEnum

from seawater.gibbs import SP_from_cndr
from seawater.gibbs import cte

# For usage: please refer to the integration tests in
# ion/processes/data/transforms/ctd/test/test_ctd_transforms.py

class SalinityTransform(TransformDataProcess):
    ''' A basic transform that receives input through a subscription,
    parses the input from a CTD, extracts the pressure value and scales it according to
    the defined algorithm. If the transform
    has an output_stream it will publish the output on the output stream.
    '''

    def on_start(self):
        super(SalinityTransform, self).on_start()
        if not self.CFG.process.publish_streams.has_key('salinity'):
            raise AssertionError("For CTD transforms, please send the stream_id "
                                 "using a special keyword (ex: salinity)")

    def recv_packet(self, packet, stream_route, stream_id):
        """
        Processes incoming data!!!!
        """
        log.info('Received incoming packet')

        if packet == {}:
            return

        granule = CTDL2SalinityTransformAlgorithm.execute(packet)

        self.salinity.publish(msg=granule)


class CTDL2SalinityTransformAlgorithm(SimpleGranuleTransformFunction):

    @staticmethod
    @SimpleGranuleTransformFunction.validate_inputs
    def execute(input=None, context=None, config=None, params=None, state=None):

        rdt = RecordDictionaryTool.load_from_granule(input)

        conductivity = rdt['conductivity']
        pressure = rdt['pressure']
        temperature = rdt['temp']

        longitude = rdt['lon']
        latitude = rdt['lat']
        time = rdt['time']
        depth = rdt['depth']

        # create parameter settings
        sal_pdict = CTDL2SalinityTransformAlgorithm._create_parameter()

        sal_value = SP_from_cndr(r=conductivity/cte.C3515, t=temperature, p=pressure)
        # build the granule for salinity
        result = CTDL2SalinityTransformAlgorithm._build_granule_settings(sal_pdict, 'salinity', sal_value, time, latitude, longitude, depth)

        return result

    @staticmethod
    def _create_parameter():

        pdict = ParameterDictionary()

        pdict = CTDL2SalinityTransformAlgorithm._add_location_time_ctxt(pdict)

        pres_ctxt = ParameterContext('salinity', param_type=QuantityType(value_encoding=np.float32))
        pres_ctxt.uom = 'unknown'
        pres_ctxt.fill_value = 0e0
        pdict.add_context(pres_ctxt)

        return pdict

    @staticmethod
    def _add_location_time_ctxt(pdict):

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

        log.debug("CTDL2SalinityTransform:_build_granule_settings: logging published Record Dictionary:\n %s", str(root_rdt.pretty_print()))
        return root_rdt.to_granule()
