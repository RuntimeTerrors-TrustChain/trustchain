import random
from faker import Faker
from rapidfuzz import fuzz
from typing import List, Dict, Tuple, Set
from config import GLOBAL_SEED

fake = Faker("en_IN")
Faker.seed(GLOBAL_SEED)
random.seed(GLOBAL_SEED)


class EntityRegistryBuilder:
    """
    Collision-free synthetic entity builder.
    Guarantees that clean entities never share director names, addresses,
    phones, or bank accounts with each other or with planted shell cartels.
    """

    def __init__(self, seed: int = GLOBAL_SEED):
        self.fake = Faker("en_IN")
        Faker.seed(seed)
        random.seed(seed)
        self.used_entity_ids: Set[str] = set()
        self.used_directors: Set[str] = set()
        self.used_addresses: Set[str] = set()
        self.used_phones: Set[str] = set()
        self.used_bank_accounts: Set[str] = set()

    def get_unique_entity_id(self) -> str:
        while True:
            eid = f"VEND-{self.fake.unique.random_int(1000, 9999)}"
            if eid not in self.used_entity_ids:
                self.used_entity_ids.add(eid)
                return eid

    def get_unique_director_name(self, max_attempts: int = 50) -> str:
        for _ in range(max_attempts):
            first = self.fake.first_name()
            last = self.fake.last_name()
            middle_initial = chr(65 + (len(self.used_directors) * 7 + _) % 26)
            name = f"{first} {middle_initial}. {last}"

            # Check exact and fuzzy similarity to prevent accidental links
            if name in self.used_directors:
                continue
            if any(
                fuzz.ratio(name, existing) >= 85.0 for existing in self.used_directors
            ):
                continue

            self.used_directors.add(name)
            return name

        # Fallback with deterministic numeric salt if name pool exhausts
        name = f"{self.fake.first_name()} {self.fake.last_name()} {len(self.used_directors) + 1}"
        self.used_directors.add(name)
        return name

    def get_unique_address(self) -> str:
        # Structured with unique building, sector, and 6-digit postal code to prevent fuzzy overlaps
        idx = len(self.used_addresses) + 1
        city = self.fake.city()
        addr = f"Unit {idx * 17 % 899 + 100}, Sector {idx % 90 + 10}, {city} - {500000 + idx}"
        self.used_addresses.add(addr)
        return addr

    def get_unique_phone(self) -> str:
        while True:
            p = f"+91-9{self.fake.unique.random_int(100000000, 999999999)}"
            if p not in self.used_phones:
                self.used_phones.add(p)
                return p

    def get_unique_bank_account(self) -> str:
        bank_prefixes = ["HDFC", "ICIC", "SBIN", "UTIB", "KKBK", "PUNB"]
        while True:
            prefix = bank_prefixes[len(self.used_bank_accounts) % len(bank_prefixes)]
            acc = f"{prefix}{self.fake.unique.random_int(10000000, 99999999)}"
            if acc not in self.used_bank_accounts:
                self.used_bank_accounts.add(acc)
                return acc

    def inject_shell_cluster(
        self, cluster_id: str, size: int = 4
    ) -> Tuple[List[Dict], Dict]:
        """Injects a tightly-linked shell company network sharing directors and addresses."""
        shared_director = self.get_unique_director_name()
        shared_address = self.get_unique_address()
        shared_bank_prefix = self.fake.bban()[:6]

        cluster_entities = []
        for _ in range(size):
            eid = self.get_unique_entity_id()
            cluster_entities.append(
                {
                    "entity_id": eid,
                    "name": self.fake.company()
                    + " "
                    + random.choice(["Global", "Holdings", "Trading", "Logistics"]),
                    "director_names": [shared_director],
                    "registered_address": shared_address,
                    "phone": self.get_unique_phone(),
                    "bank_account": f"{shared_bank_prefix}{self.fake.random_int(100000, 999999)}",
                    "registration_date": self.fake.date_between(
                        start_date="-180d", end_date="-30d"
                    ).isoformat(),
                }
            )

        ground_truth = {
            "cluster_id": cluster_id,
            "shared_director": shared_director,
            "shared_address": shared_address,
            "members": [e["entity_id"] for e in cluster_entities],
        }
        return cluster_entities, ground_truth

    def generate_clean_entities(self, count: int = 120) -> List[Dict]:
        """Generates independent, legitimate vendor entities with zero attribute collisions."""
        entities = []
        for _ in range(count):
            entities.append(
                {
                    "entity_id": self.get_unique_entity_id(),
                    "name": self.fake.company()
                    + " "
                    + random.choice(["Pvt Ltd", "LLP", "Enterprises", "Solutions"]),
                    "director_names": [
                        self.get_unique_director_name()
                        for _ in range(random.randint(1, 2))
                    ],
                    "registered_address": self.get_unique_address(),
                    "phone": self.get_unique_phone(),
                    "bank_account": self.get_unique_bank_account(),
                    "registration_date": self.fake.date_between(
                        start_date="-5y", end_date="-1y"
                    ).isoformat(),
                }
            )
        return entities


# Module-level singletons for clean imports
_builder = EntityRegistryBuilder(seed=GLOBAL_SEED)


def generate_clean_entities(count: int = 120) -> List[Dict]:
    global _builder
    return _builder.generate_clean_entities(count)


def inject_shell_cluster(cluster_id: str, size: int = 4) -> Tuple[List[Dict], Dict]:
    global _builder
    return _builder.inject_shell_cluster(cluster_id, size)


def reset_registry_builder(seed: int = GLOBAL_SEED):
    global _builder
    _builder = EntityRegistryBuilder(seed=seed)
