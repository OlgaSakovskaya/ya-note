from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from http import HTTPStatus
from pytils.translit import slugify

from notes.forms import WARNING
from notes.models import Note

User = get_user_model()


class TestNoteCreation(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.url = reverse('notes:add')
        cls.user = User.objects.create(username='Чайка')
        cls.auth_client = Client()
        cls.auth_client.force_login(cls.user)
        cls.form_data = {
            'title': 'Заголовок заметки',
            'text': 'Текст заметки',
            'slug': 'note_slug',
            'author': cls.auth_client,
        }

    def test_anonymous_user_cant_create_comment(self):
        self.client.post(self.url, data=self.form_data)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 0)

    def test_user_can_create_comment(self):
        response = self.auth_client.post(self.url, data=self.form_data)
        self.assertRedirects(response, reverse('notes:success'))
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)
        note = Note.objects.get()
        self.assertEqual(note.title, self.form_data['title'])
        self.assertEqual(note.text, self.form_data['text'])
        self.assertEqual(note.slug, self.form_data['slug'])
        self.assertEqual(note.author, self.user)


class TestCommentEditDelete(TestCase):

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
        cls.url_edit = reverse('notes:edit', args=(cls.note.slug,))
        cls.url_delete = reverse('notes:delete', args=(cls.note.slug,))
        cls.form_data = {
            'title': 'Новый заголовок заметки',
            'text': 'Новый текст заметки',
            'slug': 'new_note_slug'
        }

    def test_author_can_delete_note(self):
        response = self.author_client.delete(self.url_delete)
        self.assertRedirects(response, reverse('notes:success'))
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 0)

    def test_user_cant_delete_note_of_another_user(self):
        response = self.reader_client.delete(self.url_delete)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)

    def test_author_can_edit_note(self):
        response = self.author_client.post(self.url_edit, data=self.form_data)
        self.assertRedirects(response, reverse('notes:success'))
        self.note.refresh_from_db()
        self.assertEqual(self.note.title, self.form_data['title'])
        self.assertEqual(self.note.text, self.form_data['text'])
        self.assertEqual(self.note.slug, self.form_data['slug'])

    def test_user_cant_edit_note_of_another_user(self):
        response = self.reader_client.post(self.url_edit, data=self.form_data)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.note.refresh_from_db()
        note_from_db = Note.objects.get(id=self.note.id)
        self.assertEqual(self.note.title, note_from_db.title)
        self.assertEqual(self.note.text, note_from_db.text)
        self.assertEqual(self.note.slug, note_from_db.slug)


class TestSlugUniqEmpty(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Чайка')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)

        cls.url_add = reverse('notes:add')
        cls.form_data = {
            'title': 'Новый заголовок заметки',
            'text': 'Новый текст заметки',
            'slug': 'new_note_slug'
        }

    def test_not_unique_slug(self):
        note = Note.objects.create(
            title='Заголовок заметки',
            text='Текст заметки',
            slug='note_slug',
            author=self.author
        )
        self.form_data['slug'] = note.slug
        response = self.author_client.post(self.url_add, self.form_data)
        self.assertFormError(
            response.context['form'],
            'slug',
            errors=(note.slug + WARNING)
        )
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)

    def test_empty_slug(self):
        self.form_data.pop('slug')
        response = self.author_client.post(self.url_add, self.form_data)
        self.assertRedirects(response, reverse('notes:success'))
        self.assertEqual(Note.objects.count(), 1)
        new_note = Note.objects.get()
        expected_slug = slugify(self.form_data['title'])
        self.assertEqual(new_note.slug, expected_slug)
