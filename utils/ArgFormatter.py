# Argument Formatter
# https://github.com/HoloArchivists/TwcLazer/issues/10
class ArgumentFormatter:
    # OBJECTIVE: Use a class to translate text based upon
    # dictionaries of translations
    # EXAMPLE: %DG might translate to 'dog' so the translated
    # text would just be 'dog'.
    
    def __init__(self, prefix='$'):
        self.prefix = prefix
        self.global_dictionary = {}
        self.named_dictionaries = {}
        
    def str_translate(self, string_to_translate):
        """
        Translate the string using a dictionary

        Args:
            string_to_translate (str): string to translate
            translation_dict (str): dictionary containing all of the proper translations

        Returns:
            str: a translated string
        """

        # Translate the string to the translated text
        translated_text = string_to_translate # Create a copy to operate on
        for placeholder, translation in self.global_dictionary.items(): # Iterate over the translation dictionary
            if placeholder in translated_text: # If the placeholder is found in the string to translate,
                translation = "" if translation is None else translation # If the translation is NoneType, set it equal to "",
                translated_text = translated_text.replace(placeholder, str(translation)) # Then replace the placeholder with its translation
        return translated_text # Retun the translated text
    
    def str_translate_named(self, string_to_translate, dictionary_name_to_use):
        """
        Use a named dictionary to translate the string

        Args:
            string_to_translate (str): string to translate
            dictionary_name_to_use (str): name of dictionary to use
        """
        if self.named_dictionaries[dictionary_name_to_use] is None:
            raise ValueError(f"Unable to read dictionary '{dictionary_name_to_use}'.")
        
        translation_dictionary = self.named_dictionaries[dictionary_name_to_use]
        translated_text = string_to_translate
        for placeholder, translation in translation_dictionary.items():
            if placeholder in translated_text:
                translation = "" if translation is None else translation
                translated_text = translated_text.replace(placeholder, str(translation))
        return translated_text
    
    def add_dictionary(self, dictionary_to_add):
        """
        Add a dictionary to the global dictionary

        Args:
            dictionary_to_add (dict): the dictionary to add
        """
        for placeholder, translation in dictionary_to_add.items():
            self.global_dictionary[f"{self.prefix}{placeholder}"] = translation
            
    def add_named_dictionary(self, dictionary_to_add, dictionary_name):
        """
        Add a named dictionary that you can use by name

        Args:
            dictionary_name (str): name of the dictionary to add
            dictionary_to_add (dict): dictionary of translations to add
        """
        if dictionary_name in self.named_dictionaries.keys():
            raise ValueError(f"Cannot add Dictionary: A dictionary with the name {dictionary_name} already exists")

        temporary_dict = {}
        for placeholder, translation in dictionary_to_add.items():
            temporary_dict[f"{self.prefix}{placeholder}"] = translation
        self.named_dictionaries[dictionary_name] = temporary_dict