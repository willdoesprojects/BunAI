
if __name__ != "__main__":
    from aqt import mw
    from . import bunai

    if mw:
        mw.bunai = bunai.BunAI(mw)
else:
    print("This is an Add-On for the application Anki! Please download in order to run the add on.")
