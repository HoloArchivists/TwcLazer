# Chat Formatter py
# Convert percent strings into information

# Translation of information for strings
def strTranslate(original_text,dictionary_of_translations):
    out = original_text
    for keys,target in dictionary_of_translations.items():
        if keys in out:
            out = out.replace(keys, target)
        else:
            pass
#        trans = str.maketrans(target,dictionary_of_translations[target])
#        out = out.translate(trans)
    return out

class ChatFormatter:
    
    def FormatComments(formatString, ParsedComment):
        comment_translations = {
            "%%Ag" : ParsedComment.author_grade,
            "%%Ai" : ParsedComment.author_id,
            "%%An" : ParsedComment.author_name,
            "%%Ap" : ParsedComment.author_profile_image,
            "%%As" : ParsedComment.author_screenName,
            "%%Ca" : ParsedComment.createdAt.__str__(),
            "%%Ei" : ParsedComment.event_id.__str__(),
            "%%Et" : ParsedComment.eventType,
            "%%Nc" : ParsedComment.numComments.__str__(),
            "%%Mg" : ParsedComment.message
        }
        return strTranslate(formatString, comment_translations)
    
    def FormatGifts(formatString, ParsedComment):
        gift_translations = {
            "%%Ca" : ParsedComment.createdAt.__str__(),
            "%%Ei" : ParsedComment.event_id.__str__(),
            "%%Et" : ParsedComment.eventType,
            "%%Id" : ParsedComment.item_detailImage,
            "%%Ie" : ParsedComment.item_effectCommand.__str__(),
            "%%Ii" : ParsedComment.item_image,
            "%%In" : ParsedComment.item_name,
            "%%Is" : ParsedComment.item_showsSenderInfo.__str__(),
            "%%Mg" : ParsedComment.message,
            "%%Si" : ParsedComment.sender_id,
            "%%Sg" : ParsedComment.sender_grade.__str__(),
            "%%Sn" : ParsedComment.sender_name,
            "%%Ss" : ParsedComment.sender_screenName,
            "%%Sp" : ParsedComment.sender_profileImage
        }
        return strTranslate(formatString, gift_translations)