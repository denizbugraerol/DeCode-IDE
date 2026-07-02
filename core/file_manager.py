import os

class FileManager:
    @staticmethod
    def read_file(file_path):
        """ Verilen yoldaki dosyayı okur ve içeriğini metin olarak döndürür. """
        if not os.path.isfile(file_path):
            raise ValueError("Seçilen öğe bir dosya değil.")
            
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()

    @staticmethod
    def save_file(file_path, content):
        """ Verilen içeriği belirtilen dosyaya yazar. """
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(content)