import os


def find_image(path, name, alt=False):
    for filename in os.listdir(path):
        country, *details = filename.split('|')
        if country.lower() == name.replace(' ', '_').lower() and len(details) == (bool(alt)+1):
            return os.path.join(path, filename)


def find_hint(path, name, letter):
    for filename in os.listdir(path):
        dir_filename, ext = os.path.splitext(filename)
        if dir_filename.lower() == name.replace(' ', '_').lower():
            return os.path.join(path, filename)

    video_name = f'{letter.capitalize()}.mp4'
    return os.path.join(path, video_name)


if __name__ == '__main__':
    path = 'data/countries/images'
    print(find_image(path, 'Ukraine', alt=True))
    path = 'data/countries/hints'
    print(find_hint(path, 'One_Flew Over_the_Cuckoo’s_Nesdt', 'b'))
