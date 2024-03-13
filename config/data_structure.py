from dataclasses import dataclass, field


@dataclass
class PlatformServerInfo:
    equipment_name: str
    group_id: int
    sn: str
    status: str


@dataclass
class ServerData:
    problem_servers: list[Server] = field(default_factory=list)
    normal_servers: list[Server] = field(default_factory=list)


def gather_data():
    data = ServerData(
        problem_servers=[Server("1234", "offline"), Server("5678", "offline")],
        normal_servers=[Server("91011", "online"), Server("121314", "online")]
    )
    # Use dataclasses' asdict() for conversion to dictionary if needed
    from dataclasses import asdict
    return asdict(data)
