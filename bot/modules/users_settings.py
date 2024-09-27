from aiofiles.os import remove, path as aiopath, makedirs
from asyncio import sleep
from functools import partial
from html import escape
from io import BytesIO
from os import getcwd
from os import path as ospath
from pyrogram.filters import command, regex, create
from pyrogram.types import InputMediaPhoto
from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from time import time
from PIL import Image

from bot import (
    bot,
    IS_PREMIUM_USER,
    user_data,
    config_dict,
    MAX_SPLIT_SIZE,
    global_extension_filter,
)
from ..helper.ext_utils.bot_utils import (
    update_user_ldata,
    new_task,
    get_size_bytes,
)
from ..helper.ext_utils.db_handler import database
from ..helper.ext_utils.media_utils import create_thumb
from ..helper.telegram_helper.bot_commands import BotCommands
from ..helper.telegram_helper.button_build import ButtonMaker
from ..helper.telegram_helper.filters import CustomFilters
from ..helper.telegram_helper.message_utils import (
    send_message,
    edit_message,
    send_file,
    delete_message,
)

handler_dict = {}


async def get_user_settings(from_user):
    user_id = from_user.id
    name = from_user.mention
    buttons = ButtonMaker()
    thumbpath = f"Thumbnails/{user_id}.jpg"
    rclone_conf = f"rclone/{user_id}.conf"
    token_pickle = f"tokens/{user_id}.pickle"
    user_dict = user_data.get(user_id, {})

    if (
        user_dict.get("as_doc", False)
        or "as_doc" not in user_dict
        and config_dict["AS_DOCUMENT"]
    ):
        ltype = "DOCUMENT"
    else:
        ltype = "MEDIA"

    thumbmsg = "Exists" if await aiopath.exists(thumbpath) else "Not Exists"

    if user_dict.get("split_size", False):
        split_size = user_dict["split_size"]
    else:
        split_size = config_dict["LEECH_SPLIT_SIZE"]

    if (
        user_dict.get("equal_splits", False)
        or "equal_splits" not in user_dict
        and config_dict["EQUAL_SPLITS"]
    ):
        equal_splits = "Enabled"
    else:
        equal_splits = "Disabled"

    if (
        user_dict.get("media_group", False)
        or "media_group" not in user_dict
        and config_dict["MEDIA_GROUP"]
    ):
        media_group = "Enabled"
    else:
        media_group = "Disabled"

    if user_dict.get("lprefix", False):
        lprefix = user_dict["lprefix"]
    elif "lprefix" not in user_dict and config_dict["LEECH_FILENAME_PREFIX"]:
        lprefix = config_dict["LEECH_FILENAME_PREFIX"]
    else:
        lprefix = "None"

    if user_dict.get("leech_dest", False):
        leech_dest = user_dict["leech_dest"]
    elif "leech_dest" not in user_dict and config_dict["LEECH_DUMP_CHAT"]:
        leech_dest = config_dict["LEECH_DUMP_CHAT"]
    else:
        leech_dest = "None"

    if (
        IS_PREMIUM_USER
        and user_dict.get("user_transmission", False)
        or "user_transmission" not in user_dict
        and config_dict["USER_TRANSMISSION"]
    ):
        leech_method = "user"
    else:
        leech_method = "bot"

    if (
        IS_PREMIUM_USER
        and user_dict.get("mixed_leech", False)
        or "mixed_leech" not in user_dict
        and config_dict["MIXED_LEECH"]
    ):
        mixed_leech = "Enabled"
    else:
        mixed_leech = "Disabled"
    if user_dict.get("thumb_layout", False):
        thumb_layout = user_dict["thumb_layout"]
    elif "thumb_layout" not in user_dict and config_dict["THUMBNAIL_LAYOUT"]:
        thumb_layout = config_dict["THUMBNAIL_LAYOUT"]
    else:
        thumb_layout = "None"

    buttons.data_button("Leech Settings", f"userset {user_id} leech")

    buttons.data_button("Rclone Tools", f"userset {user_id} rclone")
    rccmsg = "Exists" if await aiopath.exists(rclone_conf) else "Not Exists"
    if user_dict.get("rclone_path", False):
        rccpath = user_dict["rclone_path"]
    elif RP := config_dict["RCLONE_PATH"]:
        rccpath = RP
    else:
        rccpath = "None"

    buttons.data_button("Gdrive Tools", f"userset {user_id} gdrive")
    tokenmsg = "Exists" if await aiopath.exists(token_pickle) else "Not Exists"
    if user_dict.get("gdrive_id", False):
        gdrive_id = user_dict["gdrive_id"]
    elif GI := config_dict["GDRIVE_ID"]:
        gdrive_id = GI
    else:
        gdrive_id = "None"
    index = user_dict["index_url"] if user_dict.get("index_url", False) else "None"
    if (
        user_dict.get("stop_duplicate", False)
        or "stop_duplicate" not in user_dict
        and config_dict["STOP_DUPLICATE"]
    ):
        sd_msg = "Enabled"
    else:
        sd_msg = "Disabled"

    upload_paths = "Added" if user_dict.get("upload_paths", False) else "None"
    buttons.data_button("Upload Paths", f"userset {user_id} upload_paths")

    default_upload = (
        user_dict.get("default_upload", "") or config_dict["DEFAULT_UPLOAD"]
    )
    du = "Gdrive ✅" if default_upload == "gd" else "Rclone ✅"
    dub = "Gdrive" if default_upload != "gd" else "Rclone"
    buttons.data_button(f"With {dub}", f"userset {user_id} {default_upload}")

    buttons.data_button("Excluded Exts", f"userset {user_id} ex_ex")
    if user_dict.get("excluded_extensions", False):
        ex_ex = user_dict["excluded_extensions"]
    elif "excluded_extensions" not in user_dict and global_extension_filter:
        ex_ex = global_extension_filter
    else:
        ex_ex = "None"

    ns_msg = "Added" if user_dict.get("name_sub", False) else "None"
    buttons.data_button("Name Subtitute", f"userset {user_id} name_substitute")

    buttons.data_button("YT-DLP Options", f"userset {user_id} yto")
    if user_dict.get("yt_opt", False):
        ytopt = user_dict["yt_opt"]
    elif "yt_opt" not in user_dict and (YTO := config_dict["YT_DLP_OPTIONS"]):
        ytopt = YTO
    else:
        ytopt = "None"

    if user_dict:
        buttons.data_button("Reset All", f"userset {user_id} reset")

    buttons.data_button("Close", f"userset {user_id} close")

    text = f"""<u>{name}'s User Settings</u>  

<code>Leech Type    :</code> {ltype}  
<code>Split Size    :</code> {split_size}  
<code>Equal Splits  :</code> {equal_splits}  
<code>Leech Method  :</code> {leech_method}  
<code>Media Group   :</code> {media_group}  
<code>Upload Paths  :</code> {upload_paths}  
<code>Stop Duplicate:</code> {sd_msg}  
<code>Default Upload:</code> {du}  
<code>YT-DLP Opts   :</code> {ytopt}
<code>Exclude Exts  :</code> {ex_ex}"""

    return text, buttons.build_menu(2)


async def update_user_settings(query):
    msg, button = await get_user_settings(query.from_user)
    user_id = query.from_user.id
    thumbnail = f"Thumbnails/{user_id}.jpg"
    if not ospath.exists(thumbnail):
        thumbnail = config_dict["THUMBNAIL_IMAGES"]
    await edit_message(query.message, msg, button, thumbnail)


@new_task
async def user_settings(_, message):
    from_user = message.from_user
    handler_dict[from_user.id] = False
    user_id = message.from_user.id
    thumbnail = f"Thumbnails/{user_id}.jpg"
    if not ospath.exists(thumbnail):
        thumbnail = config_dict["THUMBNAIL_IMAGES"]
    msg, button = await get_user_settings(from_user)
    await send_message(message, msg, button, thumbnail)


@new_task
async def set_thumb(_, message, pre_event):
    user_id = message.from_user.id
    handler_dict[user_id] = False
    des_dir = await create_thumb(message, user_id)
    update_user_ldata(user_id, "thumb", des_dir)
    await delete_message(message)
    await update_user_settings(pre_event)
    if config_dict["DATABASE_URL"]:
        await database.update_user_doc(user_id, "thumb", des_dir)


@new_task
async def add_rclone(_, message, pre_event):
    user_id = message.from_user.id
    handler_dict[user_id] = False
    rpath = f"{getcwd()}/rclone/"
    await makedirs(rpath, exist_ok=True)
    des_dir = f"{rpath}{user_id}.conf"
    await message.download(file_name=des_dir)
    update_user_ldata(user_id, "rclone_config", f"rclone/{user_id}.conf")
    await delete_message(message)
    await update_user_settings(pre_event)
    if config_dict["DATABASE_URL"]:
        await database.update_user_doc(user_id, "rclone_config", des_dir)


@new_task
async def add_token_pickle(_, message, pre_event):
    user_id = message.from_user.id
    handler_dict[user_id] = False
    tpath = f"{getcwd()}/tokens/"
    await makedirs(tpath, exist_ok=True)
    des_dir = f"{tpath}{user_id}.pickle"
    await message.download(file_name=des_dir)
    update_user_ldata(user_id, "token_pickle", f"tokens/{user_id}.pickle")
    await delete_message(message)
    await update_user_settings(pre_event)
    if config_dict["DATABASE_URL"]:
        await database.update_user_doc(user_id, "token_pickle", des_dir)


@new_task
async def delete_path(_, message, pre_event):
    user_id = message.from_user.id
    handler_dict[user_id] = False
    user_dict = user_data.get(user_id, {})
    names = message.text.split()
    for name in names:
        if name in user_dict["upload_paths"]:
            del user_dict["upload_paths"][name]
    new_value = user_dict["upload_paths"]
    update_user_ldata(user_id, "upload_paths", new_value)
    await delete_message(message)
    await update_user_settings(pre_event)
    if config_dict["DATABASE_URL"]:
        await database.update_user_doc(user_id, "upload_paths", new_value)


@new_task
async def set_option(_, message, pre_event, option):
    user_id = message.from_user.id
    handler_dict[user_id] = False
    value = message.text
    if option == "split_size":
        if not value.isdigit():
            value = get_size_bytes(value)
        value = min(int(value), MAX_SPLIT_SIZE)
    elif option == "leech_dest":
        if "|" not in value and (value.startswith("-") or value.isdigit()):
            value = int(value)
    elif option == "excluded_extensions":
        fx = value.split()
        value = ["aria2", "!qB"]
        for x in fx:
            x = x.lstrip(".")
            value.append(x.strip().lower())
    elif option == "upload_paths":
        user_dict = user_data.get(user_id, {})
        user_dict.setdefault("upload_paths", {})
        lines = value.split("/n")
        for line in lines:
            data = line.split(maxsplit=1)
            if len(data) != 2:
                await send_message(message, "Wrong format! Add <name> <path>")
                await update_user_settings(pre_event)
                return
            name, path = data
            user_dict["upload_paths"][name] = path
        value = user_dict["upload_paths"]
    update_user_ldata(user_id, option, value)
    await delete_message(message)
    await update_user_settings(pre_event)
    if config_dict["DATABASE_URL"]:
        await database.update_user_data(user_id)


async def event_handler(client, query, pfunc, photo=False, document=False):
    user_id = query.from_user.id
    handler_dict[user_id] = True
    start_time = time()

    async def event_filter(_, __, event):
        if photo:
            mtype = event.photo
        elif document:
            mtype = event.document
        else:
            mtype = event.text
        user = event.from_user or event.sender_chat
        return bool(
            user.id == user_id and event.chat.id == query.message.chat.id and mtype
        )

    handler = client.add_handler(
        MessageHandler(pfunc, filters=create(event_filter)), group=-1
    )

    while handler_dict[user_id]:
        await sleep(0.5)
        if time() - start_time > 60:
            handler_dict[user_id] = False
            await update_user_settings(query)
    client.remove_handler(*handler)


@new_task
async def edit_user_settings(client, query):
    from_user = query.from_user
    user_id = from_user.id
    name = from_user.mention
    message = query.message
    data = query.data.split()
    handler_dict[user_id] = False
    thumb_path = f"Thumbnails/{user_id}.jpg"
    rclone_conf = f"rclone/{user_id}.conf"
    token_pickle = f"tokens/{user_id}.pickle"
    user_dict = user_data.get(user_id, {})
    if user_id != int(data[1]):
        await query.answer("Not Yours!", show_alert=True)
    elif data[2] in [
        "as_doc",
        "equal_splits",
        "media_group",
        "user_transmission",
        "stop_duplicate",
        "mixed_leech",
    ]:
        update_user_ldata(user_id, data[2], data[3] == "true")
        await query.answer()
        await update_user_settings(query)
        if config_dict["DATABASE_URL"]:
            await database.update_user_data(user_id)
    elif data[2] in ["thumb", "rclone_config", "token_pickle"]:
        if data[2] == "thumb":
            fpath = thumb_path
        elif data[2] == "rclone_config":
            fpath = rclone_conf
        else:
            fpath = token_pickle
        if await aiopath.exists(fpath):
            await query.answer()
            await remove(fpath)
            update_user_ldata(user_id, data[2], "")
            await update_user_settings(query)
            if config_dict["DATABASE_URL"]:
                await database.update_user_doc(user_id, data[2])
        else:
            await query.answer("Old Settings", show_alert=True)
            await update_user_settings(query)
    elif data[2] in [
        "yt_opt",
        "lprefix",
        "index_url",
        "excluded_extensions",
        "name_sub",
        "thumb_layout",
    ]:
        await query.answer()
        update_user_ldata(user_id, data[2], "")
        await update_user_settings(query)
        if config_dict["DATABASE_URL"]:
            await database.update_user_data(user_id)
    elif data[2] in ["split_size", "leech_dest", "rclone_path", "gdrive_id"]:
        await query.answer()
        if data[2] in user_data.get(user_id, {}):
            del user_data[user_id][data[2]]
            await update_user_settings(query)
            if config_dict["DATABASE_URL"]:
                await database.update_user_data(user_id)
    elif data[2] == "leech":
        await query.answer()
        thumbpath = f"Thumbnails/{user_id}.jpg"
        buttons = ButtonMaker()
        buttons.data_button("Thumbnail", f"userset {user_id} sthumb")
        thumbmsg = "Exists" if await aiopath.exists(thumbpath) else "Not Exists"
        buttons.data_button("Leech Split Size", f"userset {user_id} lss")
        if user_dict.get("split_size", False):
            split_size = user_dict["split_size"]
        else:
            split_size = config_dict["LEECH_SPLIT_SIZE"]
        buttons.data_button("Dump Chat", f"userset {user_id} ldest")
        if user_dict.get("leech_dest", False):
            leech_dest = user_dict["leech_dest"]
        elif "leech_dest" not in user_dict and config_dict["LEECH_DUMP_CHAT"]:
            leech_dest = config_dict["LEECH_DUMP_CHAT"]
        else:
            leech_dest = "None"
        buttons.data_button("Leech Prefix", f"userset {user_id} leech_prefix")
        if user_dict.get("lprefix", False):
            lprefix = user_dict["lprefix"]
        elif "lprefix" not in user_dict and config_dict["LEECH_FILENAME_PREFIX"]:
            lprefix = config_dict["LEECH_FILENAME_PREFIX"]
        else:
            lprefix = "None"
        if (
            user_dict.get("as_doc", False)
            or "as_doc" not in user_dict
            and config_dict["AS_DOCUMENT"]
        ):
            ltype = "DOCUMENT"
            buttons.data_button("Send As Media", f"userset {user_id} as_doc false")
        else:
            ltype = "MEDIA"
            buttons.data_button("Send As Document", f"userset {user_id} as_doc true")
        if (
            user_dict.get("equal_splits", False)
            or "equal_splits" not in user_dict
            and config_dict["EQUAL_SPLITS"]
        ):
            buttons.data_button(
                "Disable Equal Splits", f"userset {user_id} equal_splits false"
            )
            equal_splits = "Enabled"
        else:
            buttons.data_button(
                "Enable Equal Splits", f"userset {user_id} equal_splits true"
            )
            equal_splits = "Disabled"
        if (
            user_dict.get("media_group", False)
            or "media_group" not in user_dict
            and config_dict["MEDIA_GROUP"]
        ):
            buttons.data_button(
                "Disable Media Group", f"userset {user_id} media_group false"
            )
            media_group = "Enabled"
        else:
            buttons.data_button(
                "Enable Media Group", f"userset {user_id} media_group true"
            )
            media_group = "Disabled"
        if (
            IS_PREMIUM_USER
            and user_dict.get("user_transmission", False)
            or "user_transmission" not in user_dict
            and config_dict["USER_TRANSMISSION"]
        ):
            buttons.data_button(
                "Leech by Bot", f"userset {user_id} user_transmission false"
            )
            leech_method = "user"
        elif IS_PREMIUM_USER:
            leech_method = "bot"
            buttons.data_button(
                "Leech by User", f"userset {user_id} user_transmission true"
            )
        else:
            leech_method = "bot"

        if (
            IS_PREMIUM_USER
            and user_dict.get("mixed_leech", False)
            or "mixed_leech" not in user_dict
            and config_dict["MIXED_LEECH"]
        ):
            mixed_leech = "Enabled"
            buttons.data_button(
                "Disable Mixed Leech", f"userset {user_id} mixed_leech false"
            )
        elif IS_PREMIUM_USER:
            mixed_leech = "Disabled"
            buttons.data_button(
                "Enable Mixed Leech", f"userset {user_id} mixed_leech true"
            )
        else:
            mixed_leech = "Disabled"

        buttons.data_button("Thumbnail Layout", f"userset {user_id} tlayout")
        if user_dict.get("thumb_layout", False):
            thumb_layout = user_dict["thumb_layout"]
        elif "thumb_layout" not in user_dict and config_dict["THUMBNAIL_LAYOUT"]:
            thumb_layout = config_dict["THUMBNAIL_LAYOUT"]
        else:
            thumb_layout = "None"

        buttons.data_button("Back", f"userset {user_id} back")
        buttons.data_button("Close", f"userset {user_id} close")
        text = f"""<u>Leech Settings for {name}</u>  
<code>Leech Type      :</code> <b>{ltype}</b>  
<code>Thumbnail       :</code> <b>{thumbmsg}</b>  
<code>Split Size      :</code> <b>{split_size}</b>  
<code>Equal Splits    :</code> <b>{equal_splits}</b>  
<code>Media Group     :</code> <b>{media_group}</b>  
<code>Prefix          :</code> <code>{escape(lprefix)}</code>  
<code>Dump Chat       :</code> <code>{leech_dest}</code>  
<code>Method          :</code> <b>{leech_method}</b>  
<code>Mixed Leech     :</code> <b>{mixed_leech}</b>  
<code>Thumbnail Layout:</code> <b>{thumb_layout}</b>  
"""

        await edit_message(message, text, buttons.build_menu(2))
    elif data[2] == "rclone":
        await query.answer()
        buttons = ButtonMaker()
        buttons.data_button("Rclone Config", f"userset {user_id} rcc")
        buttons.data_button("Default Rclone Path", f"userset {user_id} rcp")
        buttons.data_button("Back", f"userset {user_id} back")
        buttons.data_button("Close", f"userset {user_id} close")
        rccmsg = "Exists" if await aiopath.exists(rclone_conf) else "Not Exists"
        if user_dict.get("rclone_path", False):
            rccpath = user_dict["rclone_path"]
        elif RP := config_dict["RCLONE_PATH"]:
            rccpath = RP
        else:
            rccpath = "None"
        text = f"""<u>Rclone Settings for {name}</u>  
<code>Config      :</code> <b>{rccmsg}</b>  
<code>Path        :</code> <code>{rccpath}</code>  
"""
        await edit_message(message, text, buttons.build_menu(2))
    elif data[2] == "gdrive":
        await query.answer()
        buttons = ButtonMaker()
        buttons.data_button("token.pickle", f"userset {user_id} token")
        buttons.data_button("Default ID", f"userset {user_id} gdid")
        buttons.data_button("Index URL", f"userset {user_id} index")
        if (
            user_dict.get("stop_duplicate", False)
            or "stop_duplicate" not in user_dict
            and config_dict["STOP_DUPLICATE"]
        ):
            buttons.data_button(
                "Allow Duplicate", f"userset {user_id} stop_duplicate false"
            )
            sd_msg = "Enabled"
        else:
            buttons.data_button(
                "Stop Duplicate", f"userset {user_id} stop_duplicate true"
            )
            sd_msg = "Disabled"
        buttons.data_button("Back", f"userset {user_id} back")
        buttons.data_button("Close", f"userset {user_id} close")
        tokenmsg = "Exists" if await aiopath.exists(token_pickle) else "Not Exists"
        if user_dict.get("gdrive_id", False):
            gdrive_id = user_dict["gdrive_id"]
        elif GDID := config_dict["GDRIVE_ID"]:
            gdrive_id = GDID
        else:
            gdrive_id = "None"
        index = user_dict["index_url"] if user_dict.get("index_url", False) else "None"
        text = f"""<u>Gdrive Settings for {name}</u>  
<code>Token           :</code> <b>{tokenmsg}</b>  
<code>ID              :</code> <code>{gdrive_id}</code>  
<code>Index URL       :</code> <code>{index}</code>  
<code>Stop Duplicate  :</code> <b>{sd_msg}</b>  
"""
        await edit_message(message, text, buttons.build_menu(2))
    elif data[2] == "vthumb":
        await query.answer()
        await send_file(message, thumb_path, name)
        await update_user_settings(query)
    elif data[2] == "sthumb":
        await query.answer()
        buttons = ButtonMaker()
        if await aiopath.exists(thumb_path):
            buttons.data_button("View Thumbnail", f"userset {user_id} vthumb")
            buttons.data_button("Delete Thumbnail", f"userset {user_id} thumb")
        buttons.data_button("Back", f"userset {user_id} leech")
        buttons.data_button("Close", f"userset {user_id} close")
        await edit_message(
            message,
            "Send a photo to save it as custom thumbnail. Timeout: 60 sec",
            buttons.build_menu(2),
        )
        pfunc = partial(set_thumb, pre_event=query)
        await event_handler(client, query, pfunc, True)
    elif data[2] == "yto":
        await query.answer()
        buttons = ButtonMaker()
        if user_dict.get("yt_opt", False) or config_dict["YT_DLP_OPTIONS"]:
            buttons.data_button(
                "Remove YT-DLP Options", f"userset {user_id} yt_opt", "header"
            )
        buttons.data_button("Back", f"userset {user_id} back")
        buttons.data_button("Close", f"userset {user_id} close")
        rmsg = """
Send YT-DLP Options. Timeout: 60 sec
Format: key:value|key:value|key:value.
Example: format:bv*+mergeall[vcodec=none]|nocheckcertificate:True
Check all yt-dlp api options from this <a href='https://github.com/yt-dlp/yt-dlp/blob/master/yt_dlp/YoutubeDL.py#L184'>FILE</a> or use this <a href='https://t.me/mltb_official_channel/177'>script</a> to convert cli arguments to api options.
        """
        await edit_message(message, rmsg, buttons.build_menu(2))
        pfunc = partial(set_option, pre_event=query, option="yt_opt")
        await event_handler(client, query, pfunc)
    elif data[2] == "lss":
        await query.answer()
        buttons = ButtonMaker()
        if user_dict.get("split_size", False):
            buttons.data_button("Reset Split Size", f"userset {user_id} split_size")
        buttons.data_button("Back", f"userset {user_id} leech")
        buttons.data_button("Close", f"userset {user_id} close")
        await edit_message(
            message,
            f"Send Leech split size in bytes. IS_PREMIUM_USER: {IS_PREMIUM_USER}. Timeout: 60 sec",
            buttons.build_menu(2),
        )
        pfunc = partial(set_option, pre_event=query, option="split_size")
        await event_handler(client, query, pfunc)
    elif data[2] == "rcc":
        await query.answer()
        buttons = ButtonMaker()
        if await aiopath.exists(rclone_conf):
            buttons.data_button(
                "Delete rclone.conf", f"userset {user_id} rclone_config"
            )
        buttons.data_button("Back", f"userset {user_id} rclone")
        buttons.data_button("Close", f"userset {user_id} close")
        await edit_message(
            message, "Send rclone.conf. Timeout: 60 sec", buttons.build_menu(2)
        )
        pfunc = partial(add_rclone, pre_event=query)
        await event_handler(client, query, pfunc, document=True)
    elif data[2] == "rcp":
        await query.answer()
        buttons = ButtonMaker()
        if user_dict.get("rclone_path", False):
            buttons.data_button("Reset Rclone Path", f"userset {user_id} rclone_path")
        buttons.data_button("Back", f"userset {user_id} rclone")
        buttons.data_button("Close", f"userset {user_id} close")
        rmsg = "Send Rclone Path. Timeout: 60 sec"
        await edit_message(message, rmsg, buttons.build_menu(2))
        pfunc = partial(set_option, pre_event=query, option="rclone_path")
        await event_handler(client, query, pfunc)
    elif data[2] == "token":
        await query.answer()
        buttons = ButtonMaker()
        if await aiopath.exists(token_pickle):
            buttons.data_button(
                "Delete token.pickle", f"userset {user_id} token_pickle"
            )
        buttons.data_button("Back", f"userset {user_id} gdrive")
        buttons.data_button("Close", f"userset {user_id} close")
        await edit_message(
            message, "Send token.pickle. Timeout: 60 sec", buttons.build_menu(2)
        )
        pfunc = partial(add_token_pickle, pre_event=query)
        await event_handler(client, query, pfunc, document=True)
    elif data[2] == "gdid":
        await query.answer()
        buttons = ButtonMaker()
        if user_dict.get("gdrive_id", False):
            buttons.data_button("Reset Gdrive ID", f"userset {user_id} gdrive_id")
        buttons.data_button("Back", f"userset {user_id} gdrive")
        buttons.data_button("Close", f"userset {user_id} close")
        rmsg = "Send Gdrive ID. Timeout: 60 sec"
        await edit_message(message, rmsg, buttons.build_menu(2))
        pfunc = partial(set_option, pre_event=query, option="gdrive_id")
        await event_handler(client, query, pfunc)
    elif data[2] == "index":
        await query.answer()
        buttons = ButtonMaker()
        if user_dict.get("index_url", False):
            buttons.data_button("Remove Index URL", f"userset {user_id} index_url")
        buttons.data_button("Back", f"userset {user_id} gdrive")
        buttons.data_button("Close", f"userset {user_id} close")
        rmsg = "Send Index URL. Timeout: 60 sec"
        await edit_message(message, rmsg, buttons.build_menu(2))
        pfunc = partial(set_option, pre_event=query, option="index_url")
        await event_handler(client, query, pfunc)
    elif data[2] == "leech_prefix":
        await query.answer()
        buttons = ButtonMaker()
        if (
            user_dict.get("lprefix", False)
            or "lprefix" not in user_dict
            and config_dict["LEECH_FILENAME_PREFIX"]
        ):
            buttons.data_button("Remove Leech Prefix", f"userset {user_id} lprefix")
        buttons.data_button("Back", f"userset {user_id} leech")
        buttons.data_button("Close", f"userset {user_id} close")
        await edit_message(
            message,
            "Send Leech Filename Prefix. You can add HTML tags. Timeout: 60 sec",
            buttons.build_menu(2),
        )
        pfunc = partial(set_option, pre_event=query, option="lprefix")
        await event_handler(client, query, pfunc)
    elif data[2] == "ldest":
        await query.answer()
        buttons = ButtonMaker()
        if (
            user_dict.get("leech_dest", False)
            or "leech_dest" not in user_dict
            and config_dict["LEECH_DUMP_CHAT"]
        ):
            buttons.data_button(
                "Reset Leech Destination", f"userset {user_id} leech_dest",
                "header"
            )
        buttons.data_button("Back", f"userset {user_id} leech")
        buttons.data_button("Close", f"userset {user_id} close")
        await edit_message(
            message,
            "Send leech destination ID/USERNAME/PM. Timeout: 60 sec",
            buttons.build_menu(2),
        )
        pfunc = partial(set_option, pre_event=query, option="leech_dest")
        await event_handler(client, query, pfunc)
    elif data[2] == "tlayout":
        await query.answer()
        buttons = ButtonMaker()
        if (
            user_dict.get("thumb_layout", False)
            or "thumb_layout" not in user_dict
            and config_dict["THUMBNAIL_LAYOUT"]
        ):
            buttons.data_button(
                "Reset Thumbnail Layout", f"userset {user_id} thumb_layout"
            )
        buttons.data_button("Back", f"userset {user_id} leech")
        buttons.data_button("Close", f"userset {user_id} close")
        await edit_message(
            message,
            "Send thumbnail layout (widthxheight, 2x2, 3x3, 2x4, 4x4, ...). Timeout: 60 sec",
            buttons.build_menu(2),
        )
        pfunc = partial(set_option, pre_event=query, option="thumb_layout")
        await event_handler(client, query, pfunc)
    elif data[2] == "ex_ex":
        await query.answer()
        buttons = ButtonMaker()
        if (
            user_dict.get("excluded_extensions", False)
            or "excluded_extensions" not in user_dict
            and global_extension_filter
        ):
            buttons.data_button(
                "Remove Excluded Extensions", f"userset {user_id} excluded_extensions",
                "header"
            )
        buttons.data_button("Back", f"userset {user_id} back")
        buttons.data_button("Close", f"userset {user_id} close")
        await edit_message(
            message,
            "Send exluded extenions seperated by space without dot at beginning. Timeout: 60 sec",
            buttons.build_menu(2),
        )
        pfunc = partial(set_option, pre_event=query, option="excluded_extensions")
        await event_handler(client, query, pfunc)
    elif data[2] == "name_substitute":
        await query.answer()
        buttons = ButtonMaker()
        if user_dict.get("name_sub", False):
            buttons.data_button("Remove Name Subtitute", f"userset {user_id} name_sub")
        buttons.data_button("Back", f"userset {user_id} back")
        buttons.data_button("Close", f"userset {user_id} close")
        emsg = r"""Word Subtitions. You can add pattern instead of normal text. Timeout: 60 sec
NOTE: You must add \ before any character, those are the characters: \^$.|?*+()[]{}-
Example: script/code/s | mirror/leech | tea/ /s | clone | cpu/ | \[mltb\]/mltb | \\text\\/text/s
1. script will get replaced by code with sensitive case
2. mirror will get replaced by leech
4. tea will get replaced by space with sensitive case
5. clone will get removed
6. cpu will get replaced by space
7. [mltb] will get replaced by mltb
8. \text\ will get replaced by text with sensitive case
"""
        emsg += f"Your Current Value is {user_dict.get('name_sub') or 'not added yet!'}"
        await edit_message(
            message,
            emsg,
            buttons.build_menu(2),
        )
        pfunc = partial(set_option, pre_event=query, option="name_sub")
        await event_handler(client, query, pfunc)
    elif data[2] in ["gd", "rc"]:
        await query.answer()
        du = "rc" if data[2] == "gd" else "gd"
        update_user_ldata(user_id, "default_upload", du)
        await update_user_settings(query)
        if config_dict["DATABASE_URL"]:
            await database.update_user_data(user_id)
    elif data[2] == "upload_paths":
        await query.answer()
        buttons = ButtonMaker()
        buttons.data_button("New Path", f"userset {user_id} new_path")
        if user_dict.get(data[2], False):
            buttons.data_button("Show All Paths", f"userset {user_id} show_path")
            buttons.data_button("Remove Path", f"userset {user_id} rm_path")
        buttons.data_button("Back", f"userset {user_id} back")
        buttons.data_button("Close", f"userset {user_id} close")
        await edit_message(
            message,
            "Add or remove upload path.\n",
            buttons.build_menu(2),
        )
    elif data[2] == "new_path":
        await query.answer()
        buttons = ButtonMaker()
        buttons.data_button("Back", f"userset {user_id} upload_paths")
        buttons.data_button("Close", f"userset {user_id} close")
        await edit_message(
            message,
            "Send path name(no space in name) which you will use it as a shortcut and the path/id seperated by space. You can add multiple names and paths separated by new line. Timeout: 60 sec",
            buttons.build_menu(2),
        )
        pfunc = partial(set_option, pre_event=query, option="upload_paths")
        await event_handler(client, query, pfunc)
    elif data[2] == "rm_path":
        await query.answer()
        buttons = ButtonMaker()
        buttons.data_button("Back", f"userset {user_id} upload_paths")
        buttons.data_button("Close", f"userset {user_id} close")
        await edit_message(
            message,
            "Send paths names which you want to delete, separated by space. Timeout: 60 sec",
            buttons.build_menu(2),
        )
        pfunc = partial(delete_path, pre_event=query)
        await event_handler(client, query, pfunc)
    elif data[2] == "show_path":
        await query.answer()
        buttons = ButtonMaker()
        buttons.data_button("Back", f"userset {user_id} upload_paths")
        buttons.data_button("Close", f"userset {user_id} close")
        user_dict = user_data.get(user_id, {})
        msg = "".join(
            f"<b>{key}</b>: <code>{value}</code>\n"
            for key, value in user_dict["upload_paths"].items()
        )
        await edit_message(
            message,
            msg,
            buttons.build_menu(2),
        )
    elif data[2] == "reset":
        await query.answer()
        if ud := user_data.get(user_id, {}):
            if ud and ("is_sudo" in ud or "is_auth" in ud):
                for k in list(ud.keys()):
                    if k not in ["is_sudo", "is_auth"]:
                        del user_data[user_id][k]
            else:
                user_data[user_id].clear()
        await update_user_settings(query)
        if config_dict["DATABASE_URL"]:
            await database.update_user_data(user_id)
        for fpath in [thumb_path, rclone_conf, token_pickle]:
            if await aiopath.exists(fpath):
                await remove(fpath)
    elif data[2] == "back":
        await query.answer()
        await update_user_settings(query)
    else:
        await query.answer()
        await delete_message(message.reply_to_message)
        await delete_message(message)


@new_task
async def send_users_settings(_, message):
    if user_data:
        msg = ""
        for u, d in user_data.items():
            kmsg = f"\n<b>{u}:</b>\n"
            if vmsg := "".join(
                f"{k}: <code>{v}</code>\n" for k, v in d.items() if f"{v}"
            ):
                msg += kmsg + vmsg

        msg_ecd = msg.encode()
        if len(msg_ecd) > 4000:
            with BytesIO(msg_ecd) as ofile:
                ofile.name = "users_settings.txt"
                await send_file(message, ofile)
        else:
            await send_message(message, msg)
    else:
        await send_message(message, "No users data!")


bot.add_handler(
    MessageHandler(
        send_users_settings,
        filters=command(BotCommands.UsersCommand, case_sensitive=True)
        & CustomFilters.sudo,
    )
)
bot.add_handler(
    MessageHandler(
        user_settings,
        filters=command(BotCommands.UserSetCommand, case_sensitive=True)
        & CustomFilters.authorized,
    )
)
bot.add_handler(CallbackQueryHandler(edit_user_settings, filters=regex("^userset")))
