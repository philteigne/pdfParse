from datetime import *
# input01 = '(cid:45)(cid:88)(cid:81)(cid:3)(cid:20)(cid:24) (cid:36)(cid:80)(cid:68)(cid:93)(cid:82)(cid:81)(cid:3)(cid:3) (cid:4)(cid:891)(cid:891)(cid:19)(cid:24)(cid:21)(cid:28) (cid:881)(cid:7)(cid:20)(cid:24)(cid:17)(cid:27)(cid:28) (cid:7)(cid:20)(cid:28)(cid:23)(cid:17)(cid:22)(cid:28)'
# input02 = '(cid:45)(cid:88)(cid:81)(cid:3)(cid:20)(cid:26) (cid:55)(cid:85)(cid:68)(cid:81)(cid:86)(cid:73)(cid:72)(cid:85)(cid:58)(cid:76)(cid:86)(cid:72)(cid:3)(cid:3) (cid:4)(cid:891)(cid:891)(cid:22)(cid:26)(cid:24)(cid:22) (cid:881)(cid:7)(cid:20)(cid:19)(cid:21)(cid:17)(cid:25)(cid:25) (cid:7)(cid:28)(cid:20)(cid:17)(cid:26)(cid:22)'
# input03 = '(cid:45)(cid:88)(cid:81)(cid:3)(cid:20)(cid:27) (cid:54)(cid:75)(cid:82)(cid:83)(cid:76)(cid:73)(cid:92)(cid:3)(cid:3) (cid:4)(cid:891)(cid:891)(cid:22)(cid:26)(cid:24)(cid:22) (cid:881)(cid:7)(cid:20)(cid:17)(cid:19)(cid:19) (cid:7)(cid:28)(cid:19)(cid:17)(cid:26)(cid:22)'
# input04 = '(cid:45)(cid:88)(cid:81)(cid:3)(cid:21)(cid:20) (cid:41)(cid:44)(cid:53)(cid:54)(cid:55)(cid:37)(cid:36)(cid:54)(cid:40)(cid:17)(cid:44)(cid:50)(cid:15)(cid:3)(cid:44)(cid:3)(cid:49)(cid:38)(cid:17)(cid:3)(cid:3) (cid:4)(cid:891)(cid:891)(cid:19)(cid:24)(cid:21)(cid:28) (cid:881)(cid:7)(cid:22)(cid:24)(cid:17)(cid:19)(cid:19)'
# input05 = '(cid:36)(cid:48)(cid:36)(cid:61)(cid:50)(cid:49)(cid:17)(cid:38)(cid:60)(cid:57)(cid:55)(cid:38)(cid:59)(cid:21)(cid:45)(cid:50)(cid:3)(cid:3) (cid:1) (cid:36)(cid:38)(cid:43)(cid:3)(cid:44)(cid:81) (cid:7)(cid:20)(cid:15)(cid:19)(cid:27)(cid:19)(cid:17)(cid:25)(cid:25) (cid:7)(cid:20)(cid:15)(cid:20)(cid:22)(cid:25)(cid:17)(cid:22)(cid:28)'
# input06 = '(cid:55)(cid:82)(cid:87)(cid:68)(cid:79) (cid:7)(cid:20)(cid:15)(cid:20)(cid:22)(cid:25)(cid:17)(cid:22)(cid:28)'
#
# textList = input01.split('(cid:')
# newList = []
# stringList = []
#
# print(textList)
#
# for item in textList:
#     if ')' in item:
#         item = item.replace(')', '')
#     if item != '':
#         newList.append(int(item))
#     else:
#         newList.append(item)
#
# print(newList)
#
# for item in newList:
#     if item != '':
#         stringList.append(chr(item))


print(date.today())
print("2023-09-20")
