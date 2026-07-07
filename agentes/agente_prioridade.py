"""

agentes/agente_prioridade.py



Agente responsável por classificar eventos com base em suas prioridades.

"""



from core.evento import EventoCanonico

from core.tipos import PrioridadeEvento

from core.kernel import kernel



class AgentePrioridade:

    def __init__(self):

        pass



    async def processar(self, evento: EventoCanonico):

        # Implemente a lógica para classificar a prioridade do evento

        if evento.categoria == "MEDIA":

            evento.prioridade = PrioridadeEvento.ALTA # type: ignore

        elif evento.categoria == "APP_FOREGROUND":

            evento.prioridade = PrioridadeEvento.NORMAL # type: ignore

        else:

            evento.prioridade = PrioridadeEvento.BAIXA # type: ignore



       