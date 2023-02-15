from app import app, xray


class XrayStore:
    HOSTS = [
        {
            "remark": "",
            "address": "",
            "port": None
        }
    ]

    @classmethod
    def update_hosts(cls):
        from app.db import GetDB, crud

        cls.HOSTS = []
        with GetDB() as db:
            for inbound_tag in xray.config.inbounds_by_tag:
                hosts = crud.get_hosts(db, inbound_tag)
                for host in hosts:
                    cls.HOSTS.append({
                        "remark": host.remark,
                        "address": host.address,
                        "port": host.port
                    })


@app.on_event("startup")
def app_startup():
    XrayStore.update_hosts()
