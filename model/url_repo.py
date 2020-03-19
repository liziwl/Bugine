from model import util

url_cat = {
    'cloud': [
        'https://github.com/owncloud/android',
        'https://github.com/nextcloud/android',
        'https://github.com/haiwen/seadroid'
    ],
    'file': [
        'https://github.com/1hakr/AnExplorer',
        'https://github.com/TeamAmaze/AmazeFileManager',
        'https://github.com/veniosg/Dir',
        'https://github.com/SimpleMobileTools/Simple-File-Manager',
    ],
    'browser': [
        'https://github.com/mozilla-mobile/focus-android',
        'https://github.com/duckduckgo/Android',
        'https://github.com/scoute-dich/browser'
    ],
    'notes': [
        'https://github.com/vmihalachi/turbo-editor',
        'https://github.com/federicoiosue/Omni-Notes',
        'https://github.com/farmerbb/Notepad',
        'https://github.com/standardnotes/mobile',
        'https://github.com/Automattic/simplenote-android',
    ],
    'gallery': [
        'https://github.com/afollestad/photo-affix',
        'https://github.com/SimpleMobileTools/Simple-Gallery',
        'https://gitlab.com/HoraApps/LeafPic',
    ],
    'player': [
        'https://code.videolan.org/videolan/vlc-android',
        'https://github.com/mpv-android/mpv-android',
        'https://github.com/TeamNewPipe/NewPipe',
        'https://github.com/AntennaPod/AntennaPod',
    ],
    'calc': [
        'https://github.com/tranleduy2000/ncalc'
    ],
    'sms': [
        'https://github.com/signalapp/Signal-Android',
        'https://github.com/moezbhatti/qksms',
        'https://github.com/SilenceIM/Silence'
    ],
    'hub': [
        'https://github.com/k0shk0sh/FastHub',
        'https://github.com/ThirtyDegreesRay/OpenHub',
        'https://github.com/jonan/ForkHub',
        'https://github.com/slapperwan/gh4a'
    ],
    'todo': [
        'https://github.com/avjinder/Minimal-Todo',
        'https://github.com/tasks/tasks',
        'https://github.com/Jizzu/SimpleToDo',
        'https://github.com/dmfs/opentasks'
    ],
}

url_test = [
    'https://github.com/blanyal/Remindly',
    'https://github.com/danimahardhika/candybar-library',
    'https://github.com/Anasthase/TintBrowser',
    'https://github.com/harjot-oberai/MusicDNA',
    'https://github.com/mvarnagiris/financius',
    'https://github.com/Nightonke/CoCoin',
    'https://github.com/bookdash/bookdash-android-app',
    'https://github.com/QuantumBadger/RedReader',
    'https://github.com/HabitRPG/habitica-android',
    'https://github.com/hidroh/materialistic',
]

git_test = ['https://github.com/gitpoint/git-point', ]
# some_test = [
#     'https://github.com/SimpleMobileTools/Simple-File-Manager',
#     'https://github.com/pockethub/PocketHub',
#     "https://github.com/mediathekview/zapp",
#     'https://github.com/blanyal/Remindly',
#     "https://github.com/kollerlukas/Camera-Roll-Android-App"]

some_test = [
    'https://github.com/mpcjanssen/simpletask-android']

def get_url_list(github=False, gitlab=False):
    url_list = []
    for c in url_cat:
        for u in url_cat[c]:
            if "github" in u:
                if github:
                    url_list.append(u)
            else:
                if gitlab:
                    url_list.append(u)
    return url_list


def get_std_name_list(github=False, gitlab=False):
    url_list = get_url_list(github, gitlab)
    return [util.std_table_name(u, '$') for u in url_list]


def tb_name2url(tb_name):
    url_list = get_url_list(github=True, gitlab=True)
    url_list.extend(url_test)
    lookup = {util.std_table_name(u, '$'): u for u in url_list}
    return lookup[tb_name] if tb_name in lookup else None


if __name__ == '__main__':
    url_list = get_url_list(github=True, gitlab=True)

    print(url_list)
    print(len(url_list))

    std_name_list = get_std_name_list(github=True)
    print(std_name_list)
    print(len(std_name_list))

    print(tb_name2url("HoraApps$LeafPic"))
    print(tb_name2url("111"))
