from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import CustomUser
from .models import BlogPost, Category, BlogComment, BlogLike


def _user(username, role='entrepreneur'):
    u = CustomUser.objects.create_user(username=username, password='pass12345', role=role)
    return u


def _post(title='Test Post', published=True, category=None):
    return BlogPost.objects.create(
        title=title, slug=title.lower().replace(' ', '-'),
        content='Hello world content text.',
        is_published=published,
        category=category,
    )


class BlogListTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.post = _post()

    def test_list_page_renders(self):
        r = self.client.get(reverse('blog_list'))
        self.assertEqual(r.status_code, 200)

    def test_search_filters(self):
        _post('Another Article')
        r = self.client.get(reverse('blog_list') + '?q=Another')
        self.assertContains(r, 'Another Article')
        self.assertNotContains(r, 'Test Post')

    def test_unpublished_hidden(self):
        _post('Hidden Draft', published=False)
        r = self.client.get(reverse('blog_list'))
        self.assertNotContains(r, 'Hidden Draft')

    def test_category_filter(self):
        cat = Category.objects.create(name='ISO', slug='iso')
        _post('ISO Article', category=cat)
        r = self.client.get(reverse('blog_list') + '?category=iso')
        self.assertContains(r, 'ISO Article')
        self.assertNotContains(r, 'Test Post')


class BlogDetailTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.post = _post()
        self.user = _user('tester')

    def test_detail_renders(self):
        r = self.client.get(reverse('blog_detail', args=[self.post.slug]))
        self.assertEqual(r.status_code, 200)

    def test_views_count_increments(self):
        self.post.views_count = 0
        self.post.save()
        self.client.get(reverse('blog_detail', args=[self.post.slug]))
        self.post.refresh_from_db()
        self.assertEqual(self.post.views_count, 1)

    def test_draft_returns_404(self):
        draft = _post('Draft Post', published=False)
        r = self.client.get(reverse('blog_detail', args=[draft.slug]))
        self.assertEqual(r.status_code, 404)


class BlogLikeTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.post = _post()
        self.user = _user('liker')

    def test_like_requires_login(self):
        r = self.client.post(reverse('blog_toggle_like', args=[self.post.slug]))
        self.assertIn(r.status_code, [302, 403])

    def test_like_and_unlike(self):
        self.client.force_login(self.user)
        r = self.client.post(reverse('blog_toggle_like', args=[self.post.slug]))
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertTrue(data['liked'])
        self.assertEqual(data['count'], 1)

        r2 = self.client.post(reverse('blog_toggle_like', args=[self.post.slug]))
        data2 = r2.json()
        self.assertFalse(data2['liked'])
        self.assertEqual(data2['count'], 0)


class BlogCommentTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.post = _post()
        self.user = _user('commenter')

    def test_comment_requires_login(self):
        r = self.client.post(reverse('blog_add_comment', args=[self.post.slug]), {'content': 'Hello'})
        self.assertIn(r.status_code, [302, 403])

    def test_add_comment(self):
        self.client.force_login(self.user)
        r = self.client.post(reverse('blog_add_comment', args=[self.post.slug]), {'content': 'Great article!'})
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(data['content'], 'Great article!')
        self.assertEqual(BlogComment.objects.count(), 1)

    def test_empty_comment_rejected(self):
        self.client.force_login(self.user)
        r = self.client.post(reverse('blog_add_comment', args=[self.post.slug]), {'content': '  '})
        self.assertEqual(r.status_code, 400)

    def test_delete_own_comment(self):
        self.client.force_login(self.user)
        comment = BlogComment.objects.create(post=self.post, author=self.user, content='Test')
        r = self.client.post(reverse('blog_delete_comment', args=[comment.pk]))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(BlogComment.objects.count(), 0)

    def test_delete_others_comment_forbidden(self):
        other = _user('other_user')
        comment = BlogComment.objects.create(post=self.post, author=other, content='Other')
        self.client.force_login(self.user)
        r = self.client.post(reverse('blog_delete_comment', args=[comment.pk]))
        self.assertEqual(r.status_code, 403)
        self.assertEqual(BlogComment.objects.count(), 1)
