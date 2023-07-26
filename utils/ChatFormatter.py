# Chat Formatter py
# Convert percent strings into information

# Translation of information for strings
def strTranslate(original_text, dictionary_of_translations):
    out = original_text
    for key, target in dictionary_of_translations.items():
        if key in out:
            target = "" if target is None else target
            out = out.replace(key, str(target))
    return out

class ChatFormatter:
    
    def FormatComments(formatString, ParsedComment):
        comment_translations = {
            "%%Ag" : ParsedComment.author_grade,
            "%%Ai" : ParsedComment.author_id,
            "%%An" : ParsedComment.author_name,
            "%%Ap" : ParsedComment.author_profile_image,
            "%%As" : ParsedComment.author_screenName,
            "%%Ca" : str(ParsedComment.createdAt),
            "%%Ei" : str(ParsedComment.event_id),
            "%%Et" : ParsedComment.eventType,
            "%%Nc" : str(ParsedComment.numComments),
            "%%Mg" : ParsedComment.message
        }
        return strTranslate(formatString, comment_translations)
    
    def FormatGifts(formatString, ParsedComment):
        gift_translations = {
            "%%Ca" : str(ParsedComment.createdAt),
            "%%Ei" : str(ParsedComment.event_id),
            "%%Et" : ParsedComment.eventType,
            "%%Id" : ParsedComment.item_detailImage,
            "%%Ie" : str(ParsedComment.item_effectCommand),
            "%%Ii" : ParsedComment.item_image,
            "%%In" : ParsedComment.item_name,
            "%%Is" : str(ParsedComment.item_showsSenderInfo),
            "%%Mg" : ParsedComment.message,
            "%%Si" : ParsedComment.sender_id,
            "%%Sg" : str(ParsedComment.sender_grade),
            "%%Sn" : ParsedComment.sender_name,
            "%%Ss" : ParsedComment.sender_screenName,
            "%%Sp" : ParsedComment.sender_profileImage
        }
        return strTranslate(formatString, gift_translations)
