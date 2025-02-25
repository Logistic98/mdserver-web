# coding:utf-8

import sys
import io
import os
import time
import shutil

sys.path.append(os.getcwd() + "/class/core")
import mw

app_debug = False
if mw.isAppleSystem():
    app_debug = True


def getPluginName():
    return 'pureftp'


def getPluginDir():
    return mw.getPluginDir() + '/' + getPluginName()


def getServerDir():
    return mw.getServerDir() + '/' + getPluginName()


def getInitDFile():
    if app_debug:
        return '/tmp/' + getPluginName()
    return '/etc/init.d/' + getPluginName()


def getConf():
    path = getServerDir() + "/etc/pure-ftpd.conf"
    return path


def getInitDTpl():
    path = getPluginDir() + "/init.d/pure-ftpd.tpl"
    return path


def getArgs():
    args = sys.argv[2:]
    tmp = {}
    args_len = len(args)

    if args_len == 1:
        t = args[0].strip('{').strip('}')
        t = t.split(':')
        tmp[t[0]] = t[1]
    elif args_len > 1:
        for i in range(len(args)):
            t = args[i].split(':')
            tmp[t[0]] = t[1]

    return tmp


def status():
    cmd = "ps -ef|grep pure-ftpd |grep -v grep | grep -v python | awk '{print $2}'"
    data = mw.execShell(cmd)
    if data[0] == '':
        return 'stop'
    return 'start'


def contentReplace(content):
    service_path = mw.getServerDir()
    content = content.replace('{$ROOT_PATH}', mw.getRootDir())
    content = content.replace('{$SERVER_PATH}', service_path)
    return content


def initDreplace():

    file_tpl = getInitDTpl()
    service_path = os.path.dirname(os.getcwd())

    initD_path = getServerDir() + '/init.d'
    if not os.path.exists(initD_path):
        os.mkdir(initD_path)
    file_bin = initD_path + '/' + getPluginName()

    # initd replace
    if not os.path.exists(file_bin):
        content = mw.readFile(file_tpl)
        content = contentReplace(content)
        mw.writeFile(file_bin, content)
        mw.execShell('chmod +x ' + file_bin)

    pureSbinConfig = getServerDir() + "/sbin/pure-config.pl"
    if not os.path.exists(pureSbinConfig):
        pureTplConfig = getPluginDir() + "/init.d/pure-config.pl"
        content = mw.readFile(pureTplConfig)
        content = contentReplace(content)
        mw.writeFile(pureSbinConfig, content)
        mw.execShell('chmod +x ' + pureSbinConfig)

    pureFtpdConfig = getServerDir() + "/etc/pure-ftpd.conf"
    pureFtpdConfigBak = getServerDir() + "/etc/pure-ftpd.bak.conf"
    pureFtpdConfigTpl = getPluginDir() + "/conf/pure-ftpd.conf"

    if not os.path.exists(pureFtpdConfigBak):
        shutil.copyfile(pureFtpdConfig, pureFtpdConfigBak)
        content = mw.readFile(pureFtpdConfigTpl)
        content = contentReplace(content)
        mw.writeFile(pureFtpdConfig, content)

    return file_bin


def start():
    file = initDreplace()
    data = mw.execShell(file + ' start')
    if data[1] == '':
        return 'ok'
    return data[1]


def stop():
    file = initDreplace()
    data = mw.execShell(file + ' stop')
    if data[1] == '':
        return 'ok'
    return data[1]


def restart():
    file = initDreplace()
    data = mw.execShell(file + ' restart')
    if data[1] == '':
        return 'ok'
    return 'fail'


def reload():
    file = initDreplace()
    data = mw.execShell(file + ' reload')
    if data[1] == '':
        return 'ok'
    return data[1]


def initdStatus():
    if not app_debug:
        os_name = mw.getOs()
        if os_name == 'darwin':
            return "Apple Computer does not support"
    initd_bin = getInitDFile()
    if os.path.exists(initd_bin):
        return 'ok'
    return 'fail'


def initdInstall():
    import shutil
    if not app_debug:
        os_name = mw.getOs()
        if os_name == 'darwin':
            return "Apple Computer does not support"

    source_bin = initDreplace()
    initd_bin = getInitDFile()
    shutil.copyfile(source_bin, initd_bin)
    mw.execShell('chmod +x ' + initd_bin)
    mw.execShell('chkconfig --add ' + getPluginName())
    return 'ok'


def initdUinstall():
    if not app_debug:
        os_name = mw.getOs()
        if os_name == 'darwin':
            return "Apple Computer does not support"
    initd_bin = getInitDFile()
    os.remove(initd_bin)
    mw.execShell('chkconfig --del ' + getPluginName())
    return 'ok'


def pftpDB():
    file = getServerDir() + '/ftps.db'
    if not os.path.exists(file):
        conn = mw.M('ftps').dbPos(getServerDir(), 'ftps')
        csql = mw.readFile(getPluginDir() + '/conf/ftps.sql')
        csql_list = csql.split(';')
        for index in range(len(csql_list)):
            conn.execute(csql_list[index], ())
    else:
        conn = mw.M('ftps').dbPos(getServerDir(), 'ftps')
    return conn


def pftpUser():
    if mw.isAppleSystem():
        user = mw.execShell(
            "who | sed -n '2, 1p' |awk '{print $1}'")[0].strip()
        return user
    return 'www'


def pftpAdd(username, password, path):
    user = pftpUser()

    if not os.path.exists(path):
        os.makedirs(path)
        if mw.isAppleSystem():
            os.system('chown ' + user + '.staff ' + path)
        else:
            os.system('chown www.www ' + path)

    cmd = getServerDir() + '/bin/pure-pw useradd ' + username + ' -u ' + user + ' -d ' + \
        path + '<<EOF \n' + password + '\n' + password + '\nEOF'
    return mw.execShell(cmd)


def pftpMod(username, password):
    user = pftpUser()
    cmd = getServerDir() + '/bin/pure-pw passwd ' + username + \
        '<<EOF \n' + password + '\n' + password + '\nEOF'
    return mw.execShell(cmd)


def pftpStop(username):
    cmd = getServerDir() + '/bin/pure-pw usermod ' + username + ' -r 1'
    return mw.execShell(cmd)


def pftpStart(username):
    cmd = getServerDir() + '/bin/pure-pw usermod ' + username + " -r ''"
    return mw.execShell(cmd)


def pftpReload():
    mw.execShell(getServerDir() + '/bin/pure-pw mkdb ' +
                 getServerDir() + '/etc/pureftpd.pdb')


def getWwwDir():
    path = mw.getWwwDir()
    return path


def getFtpPort():
    import re
    try:
        file = getServerDir() + '/etc/pure-ftpd.conf'
        conf = mw.readFile(file)
        rep = "\n#?\s*Bind\s+[0-9]+\.[0-9]+\.[0-9]+\.+[0-9]+,([0-9]+)"
        port = re.search(rep, conf).groups()[0]
    except:
        port = '21'
    return port


def getFtpList():
    args = getArgs()
    page = 1
    page_size = 10
    search = ''
    if 'page' in args:
        page = int(args['page'])

    if 'page_size' in args:
        page_size = int(args['page_size'])

    if 'search' in args:
        search = args['search']

    data = {}
    conn = pftpDB()
    limit = str((page - 1) * page_size) + ',' + str(page_size)
    # print limit, search
    condition = ''
    if not search == '':
        condition = "name like '%" + search + "%'"
    field = 'id,pid,name,password,path,status,ps,addtime'
    clist = conn.where(condition, ()).field(
        field).limit(limit).order('id desc').select()

    count = conn.where(condition, ()).count()
    _page = {}
    _page['count'] = count
    _page['p'] = page
    _page['row'] = page_size
    _page['tojs'] = 'ftpList'
    data['page'] = mw.getPage(_page)

    info = {}
    info['ip'] = mw.getLocalIp()
    info['port'] = getFtpPort()
    data['info'] = info
    data['data'] = clist

    return mw.getJson(data)


def addFtp():
    import urllib
    args = getArgs()
    if not 'ftp_username' in args:
        return 'ftp_username missing'

    if not 'ftp_password' in args:
        return 'ftp_password missing'

    if not 'path' in args:
        return 'path missing'

    if not 'ps' in args:
        return 'ps missing'

    path = urllib.unquote(args['path'])
    user = args['ftp_username']
    pwd = args['ftp_password']
    ps = args['ps']

    addtime = time.strftime('%Y-%m-%d %X', time.localtime())

    data = pftpAdd(user, pwd, path)
    conn = pftpDB()
    conn.add('pid,name,password,path,status,ps,addtime',
             (0, user, pwd, path, 1, ps, addtime))
    pftpReload()
    if data[1] == '':
        return 'ok'
    return data[0]


def delFtp():
    args = getArgs()
    if not 'id' in args:
        return 'ftp_username missing'

    if not 'username' in args:
        return 'username missing'

    mw.execShell(getServerDir() +
                 '/bin/pure-pw userdel ' + args['username'])
    pftpReload()
    conn = pftpDB()
    conn.where("id=?", (args['id'],)).delete()
    mw.writeLog('TYPE_FTP', 'FTP_DEL_SUCCESS', (args['username'],))
    return 'ok'


def modFtp():
    args = getArgs()
    if not 'id' in args:
        return 'id missing'

    if not 'name' in args:
        return 'name missing'

    if not 'password' in args:
        return 'password missing'

    conn = pftpDB()
    data = pftpMod(args['name'], args['password'])
    pftpReload()

    conn.where('id=?', (int(args['id']),)).save(
        'password', (args['password'],))
    # print data
    if data[1] == '':
        return 'ok'
    return data[0]


def modFtpPort():
    import re
    args = getArgs()
    if not 'port' in args:
        return 'port missing'
    try:
        port = args['port']
        if int(port) < 1 or int(port) > 65535:
            return '端口范围不正确!'
        file = file = getServerDir() + '/etc/pure-ftpd.conf'
        conf = mw.readFile(file)
        rep = u"\n#?\s*Bind\s+[0-9]+\.[0-9]+\.[0-9]+\.+[0-9]+,([0-9]+)"
        # preg_match(rep,conf,tmp)
        conf = re.sub(
            rep, "\nBind                         0.0.0.0," + port, conf)
        mw.writeFile(file, conf)
        restart()
        return 'ok'
    except Exception as ex:
        return str(ex)


def stopPort():
    args = getArgs()
    if not 'id' in args:
        return 'id missing'

    if not 'username' in args:
        return 'username missing'

    if not 'status' in args:
        return 'status missing'

    data = pftpStop(args['username'])
    pftpReload()
    conn = pftpDB()
    conn.where('id=?', (int(args['id']),)).save(
        'status', (args['status'],))

    if data[1] == '':
        return 'ok'
    return data[0]


def startPort():
    args = getArgs()
    if not 'id' in args:
        return 'id missing'

    if not 'username' in args:
        return 'username missing'

    if not 'status' in args:
        return 'status missing'

    data = pftpStart(args['username'])
    pftpReload()
    conn = pftpDB()
    conn.where('id=?', (int(args['id']),)).save(
        'status', (args['status'],))

    if data[1] == '':
        return 'ok'
    return data[0]


if __name__ == "__main__":
    func = sys.argv[1]
    if func == 'status':
        print(status())
    elif func == 'start':
        print(start())
    elif func == 'stop':
        print(stop())
    elif func == 'restart':
        print(restart())
    elif func == 'reload':
        print(reload())
    elif func == 'initd_status':
        print(initdStatus())
    elif func == 'initd_install':
        print(initdInstall())
    elif func == 'initd_uninstall':
        print(initdUinstall())
    elif func == 'conf':
        print(getConf())
    elif func == 'get_www_dir':
        print(getWwwDir())
    elif func == 'get_ftp_list':
        print(getFtpList())
    elif func == 'add_ftp':
        print(addFtp())
    elif func == 'del_ftp':
        print(delFtp())
    elif func == 'mod_ftp':
        print(modFtp())
    elif func == 'mod_ftp_port':
        print(modFtpPort())
    elif func == 'stop_ftp':
        print(stopPort())
    elif func == 'start_ftp':
        print(startPort())
    else:
        print('error')
