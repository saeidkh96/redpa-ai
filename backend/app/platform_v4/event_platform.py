from __future__ import annotations
from dataclasses import dataclass, field
from .common import Registry, utcnow

@dataclass(slots=True)
class EventEnvelope:
    event_id:str
    topic:str
    tenant_id:str
    payload:dict[str,object]=field(default_factory=dict)
    attempts:int=0
    status:str="pending"
    last_error:str|None=None

class EventPlatform:
    def __init__(self)->None:self.events:Registry[EventEnvelope]=Registry(); self.dlq:Registry[EventEnvelope]=Registry()
    def publish(self,event:EventEnvelope)->EventEnvelope:return self.events.put(event.event_id,event)
    def fail(self,event_id:str,error:str,max_attempts:int=3)->EventEnvelope:
        event=self.events.get(event_id)
        if event is None:raise KeyError(event_id)
        event.attempts+=1; event.last_error=error
        if event.attempts>=max_attempts:event.status="dead-letter"; self.dlq.put(event.event_id,event)
        else:event.status="retry"
        return event
    def replay(self,event_id:str)->EventEnvelope:
        event=self.dlq.get(event_id)
        if event is None:raise KeyError(event_id)
        event.status="pending"; event.last_error=None; self.events.put(event.event_id,event); self.dlq.delete(event_id); return event
