from projects.highspeed import extract_gs_info

def project_manager(from_wxid, room, msg, message):
    # 高速公路demo
    if room and room in ['43102407502@chatroom','43749006811@chatroom']:
        ret = extract_gs_info(from_wxid,msg,model='glm-3-turbo')
        return ret
    
    return ''