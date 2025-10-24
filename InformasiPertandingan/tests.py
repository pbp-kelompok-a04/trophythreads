from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Country, Informasi
from main.models import Profile
import uuid

class InformasiPertandinganTests(TestCase):

    # siapin data dummy untuk setiap tes (user, flag, dan match)
    def setUp(self):
        self.admin_user = User.objects.create_user(username='admin', password='admin123')
        self.regular_user = User.objects.create_user(username='buyer', password='buyer123')
        self.admin_profile = Profile.objects.create(user=self.admin_user, role='admin')
        self.user_profile = Profile.objects.create(user=self.regular_user, role='user')
        
        self.spain = Country.objects.create(name='Spain', flag='https://flagcdn.com/w320/es.png')
        self.brazil = Country.objects.create(name='Brazil',flag='https://flagcdn.com/w320/br.png')
        self.indonesia = Country.objects.create(name='Indonesia', flag='https://flagcdn.com/w320/id.png')

        self.matchHot = Informasi.objects.create(title="Spain vs Brazil", date="2025-10-10",city="Madrid",country="Spain", home_team=self.spain, away_team=self.brazil,score_home_team=2,score_away_team=1,views=100)
        self.matchNoHot = Informasi.objects.create(title="Friendly Match", date="2025-10-12", city="Jakarta", country="Indonesia", home_team=self.indonesia, away_team=self.spain, score_home_team=0, score_away_team=0, views=10)

        self.client = Client()

    # tes apakah model (country dan informasi) berhasil dibuat
    def test_create_country(self):
        self.assertEqual(self.spain.name, 'Spain')
        self.assertEqual(self.spain.flag, 'https://flagcdn.com/w320/es.png')
        self.assertEqual(Country.objects.count(), 3)
        self.assertEqual(str(self.spain), "Spain")
        self.assertEqual(str(self.brazil), "Brazil")
        self.assertEqual(str(self.indonesia), "Indonesia")

    def test_create_informasi(self):
        self.assertEqual(self.matchHot.title, 'Spain vs Brazil')
        self.assertEqual(self.matchHot.date, '2025-10-10')
        self.assertEqual(self.matchHot.city, 'Madrid')
        self.assertEqual(self.matchHot.country, 'Spain')
        self.assertEqual(self.matchHot.home_team, self.spain)
        self.assertEqual(self.matchHot.away_team, self.brazil)
        self.assertEqual(self.matchHot.score_home_team, 2)
        self.assertEqual(self.matchHot.score_away_team, 1)
        self.assertEqual(self.matchHot.views, 100)
        self.assertEqual(Informasi.objects.count(), 2)
        self.assertEqual(str(self.matchHot), "Spain vs Brazil")
        self.assertEqual(str(self.matchNoHot), "Friendly Match")

    # tes method dan properti di model Informasi
    def test_is_info_hot(self):
        self.assertTrue(self.matchHot.is_info_hot) 
        self.assertFalse(self.matchNoHot.is_info_hot)

    def test_increment_views(self):
        initial_views = self.matchHot.views
        self.matchHot.increment_views()
        self.assertEqual(self.matchHot.views, initial_views + 1)
        self.matchHot.refresh_from_db()
        self.assertEqual(self.matchHot.views, 101)

    # tes tampilan
    def test_show_main(self):
        response = self.client.get(reverse('InformasiPertandingan:show_main'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'InformasiPertandingan/main.html')

    #tes perbedaan tampilan untuk admin dan user biasa
    def test_create_match(self):
        self.client.login(username='admin', password='admin123')
        response_admin = self.client.get(reverse('InformasiPertandingan:show_main'))
        self.assertEqual(response_admin.status_code, 200)
        self.assertContains(response_admin, '+ Tambah Informasi Pertandingan')
        
        self.client.login(username='buyer', password='buyer123')
        response_user = self.client.get(reverse('InformasiPertandingan:show_main'))
        self.assertEqual(response_user.status_code, 200)
        self.assertNotContains(response_user, '+ Tambah Informasi Pertandingan')

    def test_no_matches(self):
        Informasi.objects.all().delete()
        self.client.login(username='admin', password='admin123')
        response_admin_empty = self.client.get(reverse('InformasiPertandingan:show_main'))
        self.assertContains(response_admin_empty, '🔥Keep the fans updated by adding the latest match now!🔥')

        self.client.login(username='buyer', password='buyer123')
        response_user_empty = self.client.get(reverse('InformasiPertandingan:show_main'))
        self.assertNotContains(response_user_empty, '🔥Keep the fans updated by adding the latest match now!🔥')

    # tes halaman detail match user yang sudah login dan belum
    def test_match_detail(self):
        self.client.login(username='buyer', password='buyer123')
        initial_views = self.matchHot.views
        response = self.client.get(reverse('InformasiPertandingan:show_match', args=[self.matchHot.id]))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'InformasiPertandingan/match_detail.html')
        
        self.matchHot.refresh_from_db()
        self.assertEqual(self.matchHot.views, initial_views + 1)
        self.assertContains(response, 'const isAuthenticated = "True" === "True";')
        self.assertNotContains(response, 'const isAuthenticated = "false";')

    def test_match_detail_guest(self):
        initial_views = self.matchHot.views
        response = self.client.get(reverse('InformasiPertandingan:show_match', args=[self.matchHot.id]))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'InformasiPertandingan/match_detail.html')
        
        self.matchHot.refresh_from_db()
        self.assertEqual(self.matchHot.views, initial_views + 1)
        self.assertContains(response, 'const isAuthenticated = "False" === "True";')        
        self.assertNotContains(response, 'const isAuthenticated = "true";')

    # tes json
    def test_show_json(self):
        response = self.client.get(reverse('InformasiPertandingan:show_json'))
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        
        data = response.json()
        self.assertEqual(len(data), 2) 
        
        item_no_hot = None
        for item_data in data:
            if item_data['id'] == str(self.matchNoHot.id):
                item_no_hot = item_data
                break
        
        self.assertIsNotNone(item_no_hot, "Data matchNoHot tidak ditemukan di JSON response.")
        expected = {
            'id': str(self.matchNoHot.id),
            'title': 'Friendly Match',
            'home_team': {
                'name': 'Indonesia',
                'flag': 'https://flagcdn.com/w320/id.png'
            },
            'away_team': {
                'name': 'Spain',
                'flag': 'https://flagcdn.com/w320/es.png'
            },
            'score_home': 0,
            'score_away': 0,
            'is_info_hot': False
        }
        
        self.assertEqual(item_no_hot['id'], expected['id'])
        self.assertEqual(item_no_hot['title'], expected['title'])
        self.assertEqual(item_no_hot['home_team'], expected['home_team'])
        self.assertEqual(item_no_hot['away_team'], expected['away_team'])
        self.assertEqual(item_no_hot['score_home'], expected['score_home'])
        self.assertEqual(item_no_hot['score_away'], expected['score_away'])
        self.assertEqual(item_no_hot['is_info_hot'], expected['is_info_hot'])

        item_hot = None
        for item_data in data:
            if item_data['id'] == str(self.matchHot.id):
                item_hot = item_data
                break
        self.assertIsNotNone(item_hot, "Data matchHot tidak ditemukan di JSON response.")
        expected_hot = {
            'id': str(self.matchHot.id),
            'title': 'Spain vs Brazil',
            'home_team': {
                'name': 'Spain',
                'flag': 'https://flagcdn.com/w320/es.png'
            },
            'away_team': {
                'name': 'Brazil',
                'flag': 'https://flagcdn.com/w320/br.png'
            },
            'score_home': 2,
            'score_away': 1,
            'is_info_hot': True
        }
        self.assertEqual(item_hot['id'], expected_hot['id'])
        self.assertEqual(item_hot['title'], expected_hot['title'])
        self.assertEqual(item_hot['home_team'], expected_hot['home_team'])
        self.assertEqual(item_hot['away_team'], expected_hot['away_team'])
        self.assertEqual(item_hot['score_home'], expected_hot['score_home'])
        self.assertEqual(item_hot['score_away'], expected_hot['score_away'])
        self.assertEqual(item_hot['is_info_hot'], expected_hot['is_info_hot'])

    # tes json by id
    def test_show_json_by_id_endpoint(self):
        response = self.client.get(reverse('InformasiPertandingan:show_json_by_id', args=[self.matchHot.id]))
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        
        data = response.json()
        self.assertEqual(data['id'], str(self.matchHot.id))
        self.assertEqual(data['title'], 'Spain vs Brazil')
        self.assertEqual(data['home_team']['name'], 'Spain')

    # tes json by id not found  
    def test_show_json_by_id_not_found(self):
        response = self.client.get(reverse('InformasiPertandingan:show_json_by_id', args=[uuid.uuid4()]))
        self.assertEqual(response.status_code, 404)

    # tes xml
    def test_show_xml(self):
        response = self.client.get(reverse('InformasiPertandingan:show_xml'))
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/xml')
        
        content = response.content.decode('utf-8')
        self.assertIn(f'<object model="InformasiPertandingan.informasi" pk="{self.matchHot.id}"', content)
        self.assertIn(f'<object model="InformasiPertandingan.informasi" pk="{self.matchNoHot.id}"', content)
        self.assertIn('<field name="title" type="CharField">Spain vs Brazil</field>', content)
        self.assertIn('<field name="score_home_team" type="PositiveIntegerField">0</field>', content)

    # tes xml by id
    def test_show_xml_by_id_found(self):
        response = self.client.get(reverse('InformasiPertandingan:show_xml_by_id', args=[self.matchHot.id]))
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/xml')
        
        content = response.content.decode('utf-8')
        self.assertIn(f'<object model="InformasiPertandingan.informasi" pk="{self.matchHot.id}"', content)
        self.assertNotIn(f'<object pk="{self.matchNoHot.id}"', content) 
        self.assertIn('<field name="title" type="CharField">Spain vs Brazil</field>', content)
        self.assertIn('<field name="score_home_team" type="PositiveIntegerField">2</field>', content) 

    # tes xml by id not found
    def test_show_xml_by_id_not_found(self):
        response = self.client.get(reverse('InformasiPertandingan:show_xml_by_id', args=[uuid.uuid4()]))
        self.assertEqual(response.status_code, 404)
    
    # tes tambah match (admin)
    def test_add_match_as_admin(self):
        self.client.login(username='admin', password='admin123')
        
        new_match_data = {
            'title': 'New Match',
            'date': '2025-11-11',
            'city': 'Test City',
            'country': 'Test Country',
            'home_team': self.indonesia.name,
            'away_team': self.brazil.name,
            'score_home_team': 3,
            'score_away_team': 3
        }
        
        response = self.client.post(reverse('InformasiPertandingan:add_match'), data=new_match_data)
        
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Informasi.objects.count(), 3)
        self.assertTrue(Informasi.objects.filter(title='New Match').exists())
        self.assertEqual(response.json()['success'], True)

    # tes edit match (admin)
    def test_edit_match_as_admin(self):
        self.client.login(username='admin', password='admin123')
        
        edit_data = {
            'title': 'Edited Title',
            'score_home_team': 99,
            'away_team': self.spain.name
        }
        
        response = self.client.post(reverse('InformasiPertandingan:edit_match', args=[self.matchHot.id]),data=edit_data)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['success'], True)
        
        self.matchHot.refresh_from_db()
        self.assertEqual(self.matchHot.title, 'Edited Title')
        self.assertEqual(self.matchHot.score_home_team, 99)
        self.assertEqual(self.matchHot.away_team, self.spain)

    # tes hapus match (admin)
    def test_delete_match_as_admin(self):
        self.client.login(username='admin', password='admin123')
        response = self.client.get(reverse('InformasiPertandingan:delete_match', args=[self.matchHot.id]))
        self.assertRedirects(response, reverse('InformasiPertandingan:show_main'))
        self.assertEqual(Informasi.objects.count(), 1)