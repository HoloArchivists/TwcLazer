# Chat Formatter py
# Convert percent strings into information
import utils.ArgFormatter as ArgFormatter
class FileFormatter():

    def __init__(self):
        self.ArgFormatter = ArgFormatter.ArgumentFormatter(prefix='%')

    @staticmethod
    def sanitizeFilename(filename):
        bad_characters = '\\/:*?<>|"'
        return filename.translate(str.maketrans(bad_characters, "_" * len(bad_characters)))

    def FormatFilename(self, filename, translations):
        self.ArgFormatter.add_dictionary(translations)
        filename = self.ArgFormatter.str_translate(filename)
        filename = self.sanitizeFilename(filename)
        return filename 
    

class ChatFormatter:
    
    def __init__(self):
        self.ArgFormatter = ArgFormatter.ArgumentFormatter(prefix='%')
    
    def FormatComments(self, formatString, ParsedComment):
        
        comment_translations = {
            "Ag" : ParsedComment.author_grade,
            "Ai" : ParsedComment.author_id,
            "An" : ParsedComment.author_name,
            "Ap" : ParsedComment.author_profile_image,
            "As" : ParsedComment.author_screenName,
            "Ca" : str(ParsedComment.createdAt),
            "Ei" : str(ParsedComment.event_id),
            "Et" : ParsedComment.eventType,
            "Nc" : str(ParsedComment.numComments),
            "Mg" : ParsedComment.message
        }
        self.ArgFormatter.add_named_dictionary(comment_translations, "comments")
        return self.ArgFormatter.str_translate_named(formatString, "comments")
    
    def FormatGifts(self, formatString, ParsedComment):
        gift_translations = {
            "Ca" : str(ParsedComment.createdAt),
            "Ei" : str(ParsedComment.event_id),
            "Et" : ParsedComment.eventType,
            "Id" : ParsedComment.item_detailImage,
            "Ie" : str(ParsedComment.item_effectCommand),
            "Ii" : ParsedComment.item_image,
            "In" : ParsedComment.item_name,
            "Is" : str(ParsedComment.item_showsSenderInfo),
            "Mg" : ParsedComment.message,
            "Si" : ParsedComment.sender_id,
            "Sg" : str(ParsedComment.sender_grade),
            "Sn" : ParsedComment.sender_name,
            "Ss" : ParsedComment.sender_screenName,
            "Sp" : ParsedComment.sender_profileImage
        }
        self.ArgFormatter.add_named_dictionary(gift_translations, "gifts")
        return self.ArgFormatter.str_translate_named(formatString, "gifts")
