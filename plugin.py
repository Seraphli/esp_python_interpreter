from appdirs import *
import codecs
import json
import asyncio
import socketio
import uuid
import sys

APP_NAME = "electron-spirit"
PLUGIN_NAME = "ES Python"
SHORT_NAME = "py"
PLUGIN_SETTING = "plugin.setting.json"
DEFAULT_CONFIG = {"duration": 50}


class PluginApi(socketio.AsyncClientNamespace):
    def __init__(self, parent):
        super().__init__()
        self.elem_count = 0
        self.parent = parent

    async def on_connect(self):
        print("Connected")
        await self.parent.setup_connect()

    def on_disconnect(self):
        print("Disconnected")

    def on_echo(self, data):
        print("Echo:", data)

    def on_addInputHook(self, data):
        print("Add input hook:", data)

    def on_delInputHook(self, data):
        print("Del input hook:", data)

    def on_insertCSS(self, data):
        print("Insert css:", data)

    def on_removeCSS(self, data):
        print("Remove css:", data)

    def on_addElem(self, data):
        print("Add elem:", data)
        self.elem_count += 1

    def on_delElem(self, data):
        print("Remove elem:", data)
        self.elem_count -= 1

    def on_showElem(self, data):
        print("Show view:", data)

    def on_hideElem(self, data):
        print("Hide view:", data)

    def on_setBound(self, data):
        print("Set bound:", data)

    def on_setContent(self, data):
        print("Set content:", data)

    def on_setOpacity(self, data):
        print("Set opacity:", data)

    def on_execJSInElem(self, data):
        print("Exec js in elem:", data)

    def on_notify(self, data):
        print("Notify:", data)

    def on_updateBound(self, key, bound):
        print("Update bound:", key, bound)

    def on_updateOpacity(self, key, opacity):
        print("Update opacity:", key, opacity)

    async def on_processContent(self, content):
        print("Process content:", content)
        await self.parent.calc(content)

    def on_modeFlag(self, flags):
        print("Mode flag:", flags)

    def on_elemRemove(self, key):
        print("Elem remove:", key)
        # prevent remove elem
        return True

    def on_elemRefresh(self, key):
        print("Elem refresh:", key)
        # prevent refresh elem
        return True


class Plugin(object):
    def __init__(self) -> None:
        self.load_config()
        self.locals = {}
        self.globals = {}
        self.api = PluginApi(self)

    async def calc(self, content):
        try:
            res = eval(content, self.globals, self.locals)
            res = str(res) if res is not None else ""
            await sio.emit(
                "notify",
                data=(
                    {
                        "text": res,
                        "title": PLUGIN_NAME,
                        "duration": 3000 + len(res) * self.cfg["duration"],
                    },
                ),
            )
            print(res)
        except SyntaxError:
            try:
                res = exec(content, self.globals, self.locals)
                res = str(res) if res is not None else ""
                await sio.emit(
                    "notify",
                    data=(
                        {
                            "text": res,
                            "title": PLUGIN_NAME,
                            "duration": 3000 + len(res) * self.cfg["duration"],
                        },
                    ),
                )
                print(res)
            except Exception as e:
                res = str(e)
                await sio.emit(
                    "notify",
                    data=(
                        {
                            "text": res,
                            "title": PLUGIN_NAME,
                            "duration": 3000 + len(res) * self.cfg["duration"],
                            "type": "error",
                        },
                    ),
                )
                print(e)
        except Exception as e:
            res = str(e)
            await sio.emit(
                "notify",
                data=(
                    {
                        "text": res,
                        "title": PLUGIN_NAME,
                        "duration": 3000 + len(res) * self.cfg["duration"],
                        "type": "error",
                    },
                ),
            )
            print(e)

    def load_config(self):
        path = user_data_dir(APP_NAME, False, roaming=True)
        with codecs.open(path + "/api.json") as f:
            config = json.load(f)
        self.port = config["apiPort"]
        try:
            with codecs.open(PLUGIN_SETTING) as f:
                self.cfg = json.load(f)
            for k in DEFAULT_CONFIG:
                if k not in self.cfg or type(self.cfg[k]) != type(DEFAULT_CONFIG[k]):
                    self.cfg[k] = DEFAULT_CONFIG[k]
        except:
            self.cfg = DEFAULT_CONFIG
        self.save_cfg()

    def save_cfg(self):
        with codecs.open(PLUGIN_SETTING, "w") as f:
            json.dump(self.cfg, f)

    async def setup_connect(self):
        print("Setup connect")
        await sio.emit("addInputHook", data=("py"))
        await sio.emit(
            "notify",
            data=(
                {"text": "Python Interpreter started.", "title": PLUGIN_NAME},
            ),
        )
        print("Setup connect done")

    async def loop(self):
        await sio.connect(f"http://localhost:{self.port}")
        await sio.wait()


if __name__ == "__main__":
    while True:
        try:
            # asyncio
            sio = socketio.AsyncClient()
            p = Plugin()
            sio.register_namespace(p.api)
            asyncio.run(p.loop())
        except RuntimeError:
            pass
        except:
            import traceback

            traceback.print_exc()
            break
