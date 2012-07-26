#!/usr/bin/env python

"""
@package pyon.agent.common_agent 
@file pyon/agent/common_agent.py
@author Edward Hunter
@brief Common base class for ION resource agents.
"""

__author__ = 'Edward Hunter'
__license__ = 'Apache 2.0'

# Standard imports.
import traceback

# Pyon imports.
from pyon.core import bootstrap
from pyon.core.bootstrap import IonObject
from pyon.core import exception as iex
from pyon.event.event import EventPublisher
from pyon.util.log import log
from pyon.util.containers import get_ion_ts

# Pyon exceptions.
from pyon.core.exception import IonException
from pyon.core.exception import BadRequest
from pyon.core.exception import Conflict
from pyon.core.exception import Timeout
from pyon.core.exception import NotFound
from pyon.core.exception import ServerError
from pyon.core.exception import ResourceError

# Interface imports.
from interface.services.iresource_agent import BaseResourceAgent
from interface.services.iresource_agent import ResourceAgentProcessClient
from interface.objects import CapabilityType

# ION imports.
# TODO rename these to reflect base resource use.
from ion.agents.instrument.instrument_fsm import InstrumentFSM 
from ion.agents.instrument.instrument_fsm import FSMStateError
from ion.agents.instrument.common import BaseEnum


class UserAgent():
    pass

class ResourceAgentState(BaseEnum):
    """
    Resource agent common states.
    """
    POWERED_DOWN = 'RESOURCE_AGENT_STATE_POWERED_DOWN'
    UNINITIALIZED = 'RESOURCE_AGENT_STATE_UNINITIALIZED'
    INACTIVE = 'RESOURCE_AGENT_STATE_INACTIVE'
    IDLE = 'RESOURCE_AGENT_STATE_IDLE'
    STOPPED = 'RESOURCE_AGENT_STATE_STOPPED'
    COMMAND = 'RESOURCE_AGENT_STATE_COMMAND'
    STREAMING = 'RESOURCE_AGENT_STATE_STREAMING'
    TEST = 'RESOURCE_AGENT_STATE_TEST'
    CALIBRATE = 'RESOURCE_AGENT_STATE_CALIBRATE'
    DIRECT_ACCESS = 'RESOUCE_AGENT_STATE_DIRECT_ACCESS'
    BUSY = 'RESOURCE_AGENT_STATE_BUSY'

class ResourceAgentEvent(BaseEnum):
    """
    Resource agent common events.
    """
    ENTER = 'RESOURCE_AGENT_EVENT_ENTER'
    EXIT = 'RESOURCE_AGENT_EVENT_EXIT'
    POWER_UP = 'RESOURCE_AGENT_EVENT_POWER_UP'
    POWER_DOWN = 'RESOURCE_AGENT_EVENT_POWER_DOWN'
    INITIALIZE = 'RESOURCE_AGENT_EVENT_INITIALIZE'
    RESET = 'RESOURCE_AGENT_EVENT_RESET'
    GO_ACTIVE = 'RESOURCE_AGENT_EVENT_GO_ACTIVE'
    GO_INACTIVE = 'RESOURCE_AGENT_EVENT_GO_INACTIVE'
    RUN = 'RESOURCE_AGENT_EVENT_RUN'
    CLEAR = 'RESOURCE_AGENT_EVENT_CLEAR'
    PAUSE = 'RESOURCE_AGENT_EVENT_PAUSE'
    RESUME = 'RESOURCE_AGENT_EVENT_RESUME'
    GO_COMMAND = 'RESOURCE_AGENT_EVENT_GO_COMMAND'
    GO_DIRECT_ACCESS = 'RESOURCE_AGENT_EVENT_GO_DIRECT_ACCESS'
    GET_RESOURCE = 'RESOURCE_AGENT_EVENT_GET_RESOURCE'
    SET_RESOURCE = 'RESOURCE_AGENT_EVENT_SET_RESOURCE'
    EXECUTE_RESOURCE = 'RESOURCE_AGENT_EVENT_EXECUTE_RESOURCE'
    GET_RESOURCE_STATE = 'RESOURCE_AGENT_EVENT_GET_RESOURCE_STATE'
    GET_RESOURCE_CAPABILITIES = 'RESOURCE_AGENT_EVENT_GET_RESOURCE_CAPABILITIES'
    
class ResourceAgent(BaseResourceAgent):
    """
    A resource agent is an ION process of type "agent" that exposes the standard
    resource agent service interface. This base class captures the mechanisms
    common to all resource agents and is subclassed with implementations
    specific for instrument agents, user agents, etc.
    """
    
    ##############################################################
    # Class variables.
    ##############################################################

    # ION process type.
    process_type = "agent"

    # Override in subclass to publish specific types of events.
    COMMAND_EVENT_TYPE = "ResourceCommandEvent"

    # Override in subclass to set specific origin type.
    ORIGIN_TYPE = "Resource"
    
    ##############################################################
    # Constructor and ION init/deinit.
    ##############################################################    
    
    def __init__(self, *args, **kwargs):
        """
        Initialize superclass and id variables.
        """
        
        # Base class constructor.        
        super(ResourceAgent, self).__init__(*args, **kwargs)

        # The ID of the AgentInstance subtype resource object.
        self.agent_id = None

        # The ID of the AgentDefinition subtype resource object.
        self.agent_def_id = None

        # The ID of the target resource object, e.g. a device id.
        self.resource_id = None

        # UUID of the current mutex.
        self._mutex_id = None

        # Event publisher.
        self._event_publisher = None
                
        # Set intial state.        
        if 'initial_state' in kwargs:
            if ResourceAgentState.has(kwargs['initial_state']):
                self._initial_state = kwargs['initial_state']
        
        else:
            self._initial_state = ResourceAgentState.UNINITIALIZED

        # Construct the default state machine.
        self._construct_fsm()

    def _on_init(self):
        """
        ION on_init initializer called once the process exists.
        """
        log.debug("Resource Agent initializing. name=%s, resource_id=%s"
                  % (self._proc_name, self.resource_id))

        # Create event publisher.
        self._event_publisher = EventPublisher()

        # Start state machine.
        self._fsm.start(self._initial_state)

    def _on_quit(self):
        """
        ION on_quit called prior to terminating the process.
        """
        pass

    ##############################################################
    # Governance interface.
    ##############################################################    

    def negotiate(self, resource_id="", sap_in=None):
        """
        TBD.
        """
        pass

    ##############################################################
    # Capabilities interface.
    ##############################################################    

    def get_capabilities(self, resource_id="", current_state=True):
        """
        """
        
        caps = []
        agent_caps= []
        
        agent_cmds = self._fsm.get_events(current_state)
        for item in agent_cmds:
            cap = IonObject('AgentCapability',
                            name=item,
                            cap_type=CapabilityType.AGT_CMD)
            agent_caps.append(cap)

        agent_params = []
        for item in agent_params:
            cap = IonObject('AgentCapability',
                            name=item,
                            cap_type=CapabilityType.AGT_PAR)
            agent_caps.append(cap)
        
        try:
            resource_caps = self._fsm.on_event(
                ResourceAgentEvent.GET_RESOURCE_CAPABILITIES,
                current_state=current_state)
        
        except FSMStateError:
            resource_caps = []
            
        caps.extend(agent_caps)
        caps.extend(resource_caps)

        return caps
    
    ##############################################################
    # Agent interface.
    ##############################################################    

    def get_agent(self, resource_id='', params=[]):
        """
        """
        pass
    
    def set_agent(self, resource_id='', params={}):
        """
        """
        pass
    
    def get_agent_state(self, resource_id=''):
        """
        Return resource agent current common fsm state.
        """
        return self._fsm.get_current_state()

    def execute_agent(self, resource_id="", command=None):
        """
        """
        
        # Raise ION exceptions if the command is ill formed.
        if not command:
            raise iex.BadRequest('Execute argument "command" not set.')

        if not command.command:
            raise iex.BadRequest('Command name not set.')

        # Construct a command result object.
        cmd_result = IonObject("AgentCommandResult",
                               command_id=command.command_id,
                               command=command.command,
                               ts_execute=get_ion_ts(),
                               status=0)

        # Grab command syntax.
        cmd = command.command
        args = command.args or []
        kwargs = command.kwargs or {}

        try:
            cmd_result.result = self._fsm.on_event(cmd, *args, **kwargs)
        
        except FSMStateError as ex:
            raise Conflict(*(ex.args))    
                
        return cmd_result
        
    ##############################################################
    # Resource interface.
    ##############################################################    
    
    def get_resource(self, resource_id='', params=[]):
        """
        """
        
        try:
            self._fsm.on_event(ResourceAgentEvent.GET_RESOURCE, params)
            
        except FSMStateError as ex:
            raise Conflict(*(ex.args))    
    
    def set_resource(self, resource_id='', params={}):
        """
        """

        try:
            return self._fsm.on_event(ResourceAgentEvent.SET_RESOURCE, params)

        except FSMStateError as ex:
            raise Conflict(*(ex.args))    

    def get_resource_state(self, resource_id=''):
        """
        """        
        return self._fsm.on_event(ResourceAgentEvent.GET_RESOURCE_STATE)

    def execute_resource(self, resource_id="", command=None):
        """
        """
        if not command:
            raise iex.BadRequest('Execute argument "command" not set.')

        if not command.command:
            raise iex.BadRequest('Command name not set.')

        cmd_id = command.command_id
        cmd_name = command.command
        cmd_result = IonObject('AgentCommandResult', cmd_id, cmd_name)
        cmd_result.ts_execute = get_ion_ts()

        cmd_args = command.args
        cmd_kwargs = command.kwargs

        try:
            print 'IN AGENT EXECUTE RESOURCE'
            cmd_result.result = self._fsm.on_event(
                ResourceAgentEvent.EXECUTE_RESOURCE, cmd_name,
                *cmd_args, **cmd_kwargs)
            
        except FSMStateError as ex:
            raise Conflict(*(ex.args))    
        
        return cmd_result        

    ##############################################################
    # UNINITIALIZED event handlers.
    ##############################################################    

    def _handler_uninitialized_enter(self, *args, **kwargs):
        """
        """
        self._common_state_enter(*args, **kwargs)
    
    def _handler_uninitialized_exit(self, *args, **kwargs):
        """
        """
        self._common_state_exit(*args, **kwargs)

    ##############################################################
    # POWERED_DOWN event handlers.
    ##############################################################    

    def _handler_powered_down_enter(self, *args, **kwargs):
        """
        """
        self._common_state_enter(*args, **kwargs)
    
    def _handler_powered_down_exit(self, *args, **kwargs):
        """
        """
        self._common_state_exit(*args, **kwargs)

    ##############################################################
    # INACTIVE event handlers.
    ##############################################################    

    def _handler_inactive_enter(self, *args, **kwargs):
        """
        """
        self._common_state_enter(*args, **kwargs)
    
    def _handler_inactive_exit(self, *args, **kwargs):
        """
        """
        self._common_state_exit(*args, **kwargs)

    ##############################################################
    # IDLE event handlers.
    ##############################################################    

    def _handler_idle_enter(self, *args, **kwargs):
        """
        """
        self._common_state_enter(*args, **kwargs)
    
    def _handler_idle_exit(self, *args, **kwargs):
        """
        """
        self._common_state_exit(*args, **kwargs)

    ##############################################################
    # STOPPED event handlers.
    ##############################################################    

    def _handler_stopped_enter(self, *args, **kwargs):
        """
        """
        self._common_state_enter(*args, **kwargs)
    
    def _handler_stopped_exit(self, *args, **kwargs):
        """
        """
        self._common_state_exit(*args, **kwargs)

    ##############################################################
    # COMMAND event handlers.
    ##############################################################    

    def _handler_command_enter(self, *args, **kwargs):
        """
        """
        self._common_state_enter(*args, **kwargs)
    
    def _handler_command_exit(self, *args, **kwargs):
        """
        """
        self._common_state_exit(*args, **kwargs)

    ##############################################################
    # STREAMING event handlers.
    ##############################################################    

    def _handler_streaming_enter(self, *args, **kwargs):
        """
        """
        self._common_state_enter(*args, **kwargs)
    
    def _handler_streaming_exit(self, *args, **kwargs):
        """
        """
        self._common_state_exit(*args, **kwargs)

    ##############################################################
    # TEST event handlers.
    ##############################################################    

    def _handler_test_enter(self, *args, **kwargs):
        """
        """
        self._common_state_enter(*args, **kwargs)
    
    def _handler_test_exit(self, *args, **kwargs):
        """
        """
        self._common_state_exit(*args, **kwargs)

    ##############################################################
    # CALIBRATE event handlers.
    ##############################################################    

    def _handler_calibrate_enter(self, *args, **kwargs):
        """
        """
        self._common_state_enter(*args, **kwargs)
    
    def _handler_calibrate_exit(self, *args, **kwargs):
        """
        """
        self._common_state_exit(*args, **kwargs)

    ##############################################################
    # DIRECT_ACCESS event handlers.
    ##############################################################    

    def _handler_direct_access_enter(self, *args, **kwargs):
        """
        """
        self._common_state_enter(*args, **kwargs)
    
    def _handler_direct_access_exit(self, *args, **kwargs):
        """
        """
        self._common_state_exit(*args, **kwargs)

    ##############################################################
    # BUSY event handlers.
    ##############################################################

    def _handler_busy_enter(self, *args, **kwargs):
        """
        """
        self._common_state_enter(*args, **kwargs)
    
    def _handler_busy_exit(self, *args, **kwargs):
        """
        """
        self._common_state_exit(*args, **kwargs)
    
    ##############################################################
    # Helpers.
    ##############################################################    
    
    def _common_state_enter(self, *args, **kwargs):
        """
        Common work upon every state entry.
        """
        state = self._fsm.get_current_state()
        desc_str = 'Resource agent %s entered state: %s' % (self.id, state)
        log.info(desc_str)
        
        #TODO add state change publication here.
        #pub = EventPublisher('DeviceCommonLifecycleEvent')
        #pub.publish_event(origin=self.resource_id, description=desc_str)

    def _common_state_exit(self, *args, **kwargs):
        """
        Common work upon every state exit.
        """
        state = self._fsm.get_current_state()
        desc_str = 'Resource agent %s leaving state: %s' % (self.id, state)
        log.info(desc_str)
        #pub = EventPublisher('DeviceCommonLifecycleEvent')
        #pub.publish_event(origin=self.resource_id, description=desc_str)
    
    def _construct_fsm(self):
        """
        Construct the state machine and register default handlers.
        Override in subclass to add handlers for resouce-dependent behaviors
        and state transitions.
        """
                
        # Instrument agent state machine.
        self._fsm = InstrumentFSM(ResourceAgentState, ResourceAgentEvent,
                            ResourceAgentEvent.ENTER, ResourceAgentEvent.EXIT)
        
        self._fsm.add_handler(ResourceAgentState.UNINITIALIZED, ResourceAgentEvent.ENTER, self._handler_uninitialized_enter)
        self._fsm.add_handler(ResourceAgentState.UNINITIALIZED, ResourceAgentEvent.EXIT, self._handler_uninitialized_exit)

        self._fsm.add_handler(ResourceAgentState.POWERED_DOWN, ResourceAgentEvent.ENTER, self._handler_powered_down_enter)
        self._fsm.add_handler(ResourceAgentState.POWERED_DOWN, ResourceAgentEvent.EXIT, self._handler_powered_down_exit)

        self._fsm.add_handler(ResourceAgentState.INACTIVE, ResourceAgentEvent.ENTER, self._handler_inactive_enter)
        self._fsm.add_handler(ResourceAgentState.INACTIVE, ResourceAgentEvent.EXIT, self._handler_inactive_exit)

        self._fsm.add_handler(ResourceAgentState.IDLE, ResourceAgentEvent.ENTER, self._handler_idle_enter)
        self._fsm.add_handler(ResourceAgentState.IDLE, ResourceAgentEvent.EXIT, self._handler_idle_exit)

        self._fsm.add_handler(ResourceAgentState.STOPPED, ResourceAgentEvent.ENTER, self._handler_stopped_enter)
        self._fsm.add_handler(ResourceAgentState.STOPPED, ResourceAgentEvent.EXIT, self._handler_stopped_exit)

        self._fsm.add_handler(ResourceAgentState.COMMAND, ResourceAgentEvent.ENTER, self._handler_command_enter)
        self._fsm.add_handler(ResourceAgentState.COMMAND, ResourceAgentEvent.EXIT, self._handler_command_exit)
        
        self._fsm.add_handler(ResourceAgentState.STREAMING, ResourceAgentEvent.ENTER, self._handler_streaming_enter)
        self._fsm.add_handler(ResourceAgentState.STREAMING, ResourceAgentEvent.EXIT, self._handler_streaming_exit)
        
        self._fsm.add_handler(ResourceAgentState.TEST, ResourceAgentEvent.ENTER, self._handler_test_enter)
        self._fsm.add_handler(ResourceAgentState.TEST, ResourceAgentEvent.EXIT, self._handler_test_exit)
        
        self._fsm.add_handler(ResourceAgentState.CALIBRATE, ResourceAgentEvent.ENTER, self._handler_calibrate_enter)
        self._fsm.add_handler(ResourceAgentState.CALIBRATE, ResourceAgentEvent.EXIT, self._handler_calibrate_exit)
        
        self._fsm.add_handler(ResourceAgentState.DIRECT_ACCESS, ResourceAgentEvent.ENTER, self._handler_direct_access_enter)
        self._fsm.add_handler(ResourceAgentState.DIRECT_ACCESS, ResourceAgentEvent.EXIT, self._handler_direct_access_exit)
        
        self._fsm.add_handler(ResourceAgentState.BUSY, ResourceAgentEvent.ENTER, self._handler_busy_enter)
        self._fsm.add_handler(ResourceAgentState.BUSY, ResourceAgentEvent.EXIT, self._handler_busy_exit)
    
class ResourceAgentClient(ResourceAgentProcessClient):
    """
    Generic client for resource agents.
    """
    def __init__(self, resource_id, *args, **kwargs):
        """
        Client constructor.
        @param resource_id The ID this service represents.
        @param name Use this kwarg to set the target exchange name
        (service or process).
        """
        
        # Assert and set the resource ID.
        assert resource_id, "resource_id must be set for an agent"
        self.resource_id = resource_id

        # Set the name, retrieve as proc ID if not set by user.
        if not 'name' in kwargs:
            process_id = self._get_agent_process_id(self.resource_id)
            if process_id:
                kwargs['name'] = process_id
                log.debug("Use agent process %s for resource_id=%s" % (process_id, self.resource_id))
            else:
                # TODO: Check if there is a service for this type of resource
                log.debug("No agent process found for resource_id %s" % self.resource_id)
                raise iex.NotFound("No agent process found for resource_id %s" % self.resource_id)

        assert "name" in kwargs, "Name argument for agent target not set"
        
        # Superclass constructor.
        ResourceAgentProcessClient.__init__(self, *args, **kwargs)

    ##############################################################
    # Client interface.
    ##############################################################    

    def negotiate(self, *args, **kwargs):
        return super(ResourceAgentClient, self).negotiate(self.resource_id, *args, **kwargs)

    def get_capabilities(self, *args, **kwargs):
        return super(ResourceAgentClient, self).get_capabilities(self.resource_id, *args, **kwargs)

    def execute_agent(self, *args, **kwargs):
        return super(ResourceAgentClient, self).execute_agent(self.resource_id, *args, **kwargs)

    def get_agent(self, *args, **kwargs):
        return super(ResourceAgentClient, self).get_agent(self.resource_id, *args, **kwargs)

    def set_agent(self, *args, **kwargs):
        return super(ResourceAgentClient, self).set_agent(self.resource_id, *args, **kwargs)

    def get_agent_state(self, *args, **kwargs):
        return super(ResourceAgentClient, self).get_agent_state(self.resource_id, *args, **kwargs)

    def execute_resource(self, *args, **kwargs):
        print 'IN EXE RESOURCE CLIENT'
        print str(*args)
        print str(**kwargs)
        return super(ResourceAgentClient, self).execute_resource(self.resource_id, *args, **kwargs)

    def get_resource(self, *args, **kwargs):
        return super(ResourceAgentClient, self).get_resource(self.resource_id, *args, **kwargs)

    def set_resource(self, *args, **kwargs):
        return super(ResourceAgentClient, self).set_resource(self.resource_id, *args, **kwargs)

    def get_resource_state(self, *args, **kwargs):
        return super(ResourceAgentClient, self).get_resource_state(self.resource_id, *args, **kwargs)

    def emit(self, *args, **kwargs):
        return super(ResourceAgentClient, self).emit(self.resource_id, *args, **kwargs)

    ##############################################################
    # Helpers.
    ##############################################################    

    @classmethod
    def _get_agent_process_id(cls, resource_id):
        """
        Retrun the agent container proc id given the resource_id.
        """
        agent_procs = bootstrap.container_instance.directory.find_by_value('/Agents', 'resource_id', resource_id)
        if agent_procs:
            if len(agent_procs) > 1:
                log.warn("Inconsistency: More than one agent registered for resource_id=%s: %s" % (
                    resource_id, agent_procs))
            agent_id = agent_procs[0].key
            return str(agent_id)
        return None