"""
agentes/agente_contexto_sistema.py

Agente especializado em processar eventos de contexto do sistema operacional,
como localização, conectividade e outros sensores.
"""
import logging

from core.evento import EventoCanonico
from servicos.memoria_perfil import memoria_perfil

logger = logging.getLogger(__name__)

class AgenteContextoSistema:
    """
    Este agente observa os dados brutos dos sensores do sistema (enviados pelo Android)
    e os registra na memória de perfil para inferências futuras.
    """
    async def processar(self, evento: EventoCanonico):
        payload = evento.payload
        logger.info(f"🧠 [Contexto Sistema] Processando dados de sensores: {list(payload.keys())}")

        # 1. Processar informações de Wi-Fi
        wifi_info = payload.get("wifi")
        if isinstance(wifi_info, dict):
            ssid = wifi_info.get("ssid")
            # Ignora SSIDs padrões ou ocultos que não agregam valor
            if ssid and ssid not in ["<unknown ssid>", "HIDDEN_BY_OS"]:
                logger.info(f"💾 Registrando conexão com Wi-Fi: {ssid}")
                await memoria_perfil.registrar_conexao_wifi(ssid)

        # 2. Processar informações de Localização (Futuro)
        location_info = payload.get("location")
        if isinstance(location_info, dict) and "lat" in location_info:
            # TODO: Implementar lógica para agrupar localizações e inferir
            #       locais importantes (casa, trabalho).
            lat = location_info.get('lat')
            lon = location_info.get('lon')
            logger.info(f"📍 Localização recebida: Lat={lat}, Lon={lon}. Lógica de perfil ainda não implementada.")

        # 3. Processar informações de Conectividade (Futuro)
        connectivity_info = payload.get("connectivity")
        if isinstance(connectivity_info, dict):
            # TODO: A lógica de conectividade pode ser usada para decidir
            #       quando executar tarefas pesadas (ex: apenas em Wi-Fi).
            is_on_wifi = connectivity_info.get('is_wifi')
            logger.info(f"📶 Status de conectividade recebido. Wi-Fi: {is_on_wifi}. Lógica de perfil ainda não implementada.")