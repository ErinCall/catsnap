from tests import TestCase
from nose.tools import eq_
from catsnap.table.tag import Tag
from catsnap.table.image_tag import ImageTag
from catsnap.table.image import Image
from catsnap import Client

class TestTag(TestCase):
    def test_get_filenames(self):
        session = Client().session()
        dog = Image(filename='D06')
        cat = Image(filename='CA7')
        session.add(dog)
        session.add(cat)
        pet = Tag(name='pet')
        session.add(pet)
        session.flush()
        session.add(ImageTag(image_id=cat.image_id, tag_id=pet.tag_id))
        session.add(ImageTag(image_id=dog.image_id, tag_id=pet.tag_id))
        session.flush()

        filenames = pet.get_filenames()
        eq_(list(filenames), ['D06', 'CA7'])

class TestGetImageData(TestCase):
    def setup_test_data(self):

        session = Client().session()

        dog = Image(filename='D06', title='my dog')
        cat = Image(filename='CA7')
        stegosaurus = Image(filename='57E60')
        session.add(dog)
        session.add(cat)
        session.add(stegosaurus)
        pet = Tag(name='pet')
        session.add(pet)
        cool = Tag(name='cool')
        session.add(cool)
        session.flush()
        session.add(ImageTag(image_id=cat.image_id, tag_id=pet.tag_id))
        session.add(ImageTag(image_id=cat.image_id, tag_id=cool.tag_id))
        session.add(ImageTag(image_id=dog.image_id, tag_id=pet.tag_id))
        session.add(ImageTag(image_id=stegosaurus.image_id, tag_id=cool.tag_id))
        session.flush()

        return (dog, cat, stegosaurus)

    def test_a_simple_query(self):
        (dog, cat, stegosaurus) = self.setup_test_data()
        image_data = Tag.get_image_data(['pet'])
        eq_(list(image_data), [
                ('CA7', cat.image_id, 'pet cool'),
                ('D06', dog.image_id, 'my dog')])

    def test_multiple_tags(self):
        (dog, cat, stegosaurus) = self.setup_test_data()
        image_data = Tag.get_image_data(['pet','cool'])
        eq_(list(image_data), [
                ('57E60', stegosaurus.image_id, 'cool'),
                ('CA7',   cat.image_id,         'pet cool'),
                ('D06',   dog.image_id,         'my dog')])
