from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from notes.forms import NoteForm
from notes.models import Note


User = get_user_model()


class TestNoteList(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Чайка')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.reader = User.objects.create(username='Хлебные крошки')
        cls.reader_client = Client()
        cls.reader_client.force_login(cls.reader)
        cls.note = Note.objects.create(
            title='Заголовок заметки',
            text='Текст заметки',
            slug='note_slug',
            author=cls.author
        )
        cls.url_notes_list = reverse('notes:list')
        cls.url_edit = reverse('notes:edit', args=(cls.note.slug,))
        cls.url_add = reverse('notes:add')

    def test_notes_list_for_different_users(self):
        routes_list = (
            (self.author_client, True),
            (self.reader_client, False)
        )
        for client, note_in_list in routes_list:
            response = client.get(self.url_notes_list)
            object_list = response.context['object_list']
            self.assertEqual((self.note in object_list), note_in_list)

    def test_pages_contains_form(self):
        urls = (
            self.url_edit,
            self.url_add
        )
        for url in urls:
            response = self.author_client.get(url)
            self.assertIn('form', response.context)
            self.assertIsInstance(response.context['form'], NoteForm)
