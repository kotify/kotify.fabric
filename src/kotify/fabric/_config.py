class Config:
    def __init__(self, context):
        self.context = context

    @property
    def database_local_dump(self):
        return self.context.get("database", {}).get("local_dump", "dump/dump.db")
