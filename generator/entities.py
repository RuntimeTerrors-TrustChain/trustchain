import random
from faker import Faker
from typing import List, Dict, Tuple
from config import GLOBAL_SEED

fake = Faker('en_IN')
Faker.seed(GLOBAL_SEED)
random.seed(GLOBAL_SEED)

def generate_clean_entities(count: int = 120) -> List[Dict]:
    """Generates independent, legitimate vendor entities with neutral IDs."""
    entities = []
    for _ in range(count):
        entities.append({
            "entity_id": f"VEND-{fake.unique.random_int(1000, 9999)}",
            "name": fake.company() + " " + random.choice(["Pvt Ltd", "LLP", "Enterprises", "Solutions"]),
            "director_names": [fake.name() for _ in range(random.randint(1, 3))],
            "registered_address": fake.address().replace("\n", ", "),
            "phone": f"+91-{fake.msisdn()[:10]}",
            "bank_account": fake.bban(),
            "registration_date": fake.date_between(start_date='-5y', end_date='-1y').isoformat(),
        })
    return entities

def inject_shell_cluster(cluster_id: str, size: int = 4) -> Tuple[List[Dict], Dict]:
    """
    Injects a tightly-linked shell company network sharing directors and addresses.
    Uses completely neutral entity IDs to prevent label leakage.
    """
    shared_director = fake.name()
    shared_address = fake.address().replace("\n", ", ")
    shared_bank_prefix = fake.bban()[:6]
    
    cluster_entities = []
    for _ in range(size):
        cluster_entities.append({
            "entity_id": f"VEND-{fake.unique.random_int(1000, 9999)}",
            "name": fake.company() + " " + random.choice(["Global", "Holdings", "Trading", "Logistics"]),
            "director_names": [shared_director, fake.name()],
            "registered_address": shared_address,
            "phone": f"+91-{fake.msisdn()[:10]}",
            "bank_account": f"{shared_bank_prefix}{fake.random_int(100000, 999999)}",
            "registration_date": fake.date_between(start_date='-180d', end_date='-30d').isoformat(),
        })
        
    ground_truth = {
        "cluster_id": cluster_id,
        "shared_director": shared_director,
        "shared_address": shared_address,
        "members": [e["entity_id"] for e in cluster_entities]
    }
    
    return cluster_entities, ground_truth