import os


def find_image(path, name, alt=False):
    for filename in os.listdir(path):
        country, *details = filename.split('|')
        if country.lower() == name.replace(' ', '_').lower() and len(details) == (bool(alt)+1):
            return os.path.join(path, filename)


if __name__ == '__main__':
    path = 'data/countries/images'
    print(find_image(path, 'Ukraine', alt=True))
