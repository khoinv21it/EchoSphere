"""Auto-discover and load all music command modules in this package.
Each module that exposes a `setup(bot)` function will be called. If not present,
we'll attempt to instantiate any Cog subclasses found in the module as a fallback.
"""
import asyncio
import pkgutil
import importlib
import inspect
from discord.ext import commands

PACKAGE = 'app.modules.music.commands'

async def setup(bot: commands.Bot):
    pkg = importlib.import_module(PACKAGE)
    for finder, name, ispkg in pkgutil.iter_modules(pkg.__path__):
        if name.startswith('_'):
            continue
        try:
            before = set(c.name for c in bot.commands)
            module = importlib.import_module(f"{PACKAGE}.{name}")
            setup_fn = getattr(module, 'setup', None)
            if setup_fn:
                if asyncio.iscoroutinefunction(setup_fn):
                    await setup_fn(bot)
                else:
                    setup_fn(bot)
            else:
                # fallback: find Cog subclasses and register them
                added = False
                for attr in dir(module):
                    obj = getattr(module, attr)
                    if inspect.isclass(obj) and issubclass(obj, commands.Cog) and obj is not commands.Cog:
                        try:
                            if asyncio.iscoroutinefunction(getattr(obj, 'setup', None)):
                                # unlikely, but respect class-level setup convention
                                await obj.setup(bot)
                            else:
                                await bot.add_cog(obj(bot))
                                added = True
                        except Exception as e:
                            print(f"Failed to add Cog {obj} from {name}:", e)
                if not added:
                    print(f"Module {name} has no setup() function and no Cog subclasses; skipping")
                    continue
            after = set(c.name for c in bot.commands)
            new = after - before
            print(f"Loaded module {name}; new commands: {sorted(list(new))}")
        except Exception as e:
            print(f"Failed to load music command module '{name}':", e)

    # ensure debug commands always available for diagnostics
    try:
        module = importlib.import_module(f"{PACKAGE}.debug")
        setup_fn = getattr(module, 'setup', None)
        if setup_fn:
            if asyncio.iscoroutinefunction(setup_fn):
                await setup_fn(bot)
            else:
                setup_fn(bot)
    except Exception:
        pass

