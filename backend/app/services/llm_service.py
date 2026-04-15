import json
import re
from pathlib import Path
from typing import Any, Dict

import requests

from app.config import settings


class LLMService:
    def __init__(self) -> None:
        self.menu_path = Path(__file__).resolve().parent.parent.parent / 'data' / 'menu.json'

    def detect_intent(self, message: str) -> str:
        lower = message.lower()
        menu_keywords = ('menu', 'plato', 'carta', 'postre', 'ingrediente', 'vegano', 'sin gluten', 'alergia', 'alergeno', 'intolerancia', 'lactosa', 'marisco', 'celíaco')
        return 'menu_qa' if any(k in lower for k in menu_keywords) else 'reservation'

    def extract_reservation_slots(self, message: str) -> Dict[str, Any]:
        date_match = re.search(r'(\d{4}-\d{2}-\d{2})', message)
        time_match = re.search(r'(\d{1,2}:\d{2})', message)
        party_match = re.search(r'(\d+)\s*(personas|comensales|pax)', message.lower())
        phone_match = re.search(r'(\+?\d[\d\s-]{7,})', message)
        email_match = re.search(r'([\w.-]+@[\w.-]+\.\w+)', message)

        return {
            'date': date_match.group(1) if date_match else None,
            'time': time_match.group(1) if time_match else None,
            'party_size': int(party_match.group(1)) if party_match else None,
            'phone': phone_match.group(1).replace(' ', '').replace('-', '') if phone_match else None,
            'email': email_match.group(1) if email_match else None,
        }

    def ask_menu(self, question: str) -> str:
        menu_data = {}
        if self.menu_path.exists():
            menu_data = json.loads(self.menu_path.read_text(encoding='utf-8'))

        prompt = (
            'Eres el sumiller y asistente experto del restaurante gastronómico Nómada en Madrid.\n'
            'Tu tarea es resolver dudas sobre el menú y gestionar reservas amablemente en español.\n'
            'INSTRUCCIONES CLAVES SOBRE ALERGIAS:\n'
            '1. Si el cliente menciona una alergia o restricción (ej: gluten, lactosa, marisco, etc.), revisa meticulosamente los "alergenos" de cada plato en la información.\n'
            '2. Si el menú por el que se interesan tiene ese alérgeno y no se puede adaptar (mira si adaptable_sin_gluten o adaptable_vegano es true/false), avísalo explícitamente.\n'
            '3. PROPÓN PROACTIVAMENTE otros menús degustación que NO tengan ese alérgeno o sean plenamente adaptables.\n'
            '4. Si no están seguros, pregúntales qué estilo de menú buscan (mar, brasa, vegetal, homenaje histórico) e invítales a probar nuestra experiencia.\n'
            f'\nBASE_DATOS_MENUS: {json.dumps(menu_data.get("menus_degustacion", []), ensure_ascii=False)}\n\n'
            f'MENSAJE_DEL_CLIENTE: {question}'
        )

        try:
            response = requests.post(
                f'{settings.ollama_base_url}/api/generate',
                json={
                    'model': settings.ollama_model,
                    'prompt': prompt,
                    'stream': False,
                },
                timeout=20,
            )
            if response.ok:
                body = response.json()
                text = (body.get('response') or '').strip()
                if text:
                    return text
        except requests.RequestException:
            pass

        platos = menu_data.get('platos', [])
        if not platos:
            return 'No tengo el menu cargado todavia.'
        nombres = [str(p.get('nombre', 'plato')) for p in platos[:5]]
        return 'Ahora mismo estoy en modo basico. Tenemos: ' + ', '.join(nombres)
