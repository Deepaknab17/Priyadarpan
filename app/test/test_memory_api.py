from app.test.base import BaseAPITestCase
from app.models import Memory
from django.contrib.auth.models import User
from app.models import Tenant, Profile, Memory

class MemoryAPITest(BaseAPITestCase):

    def test_authenticated_user_can_create_memory(self):

        self.client.force_authenticate(
            user=self.user
        )

        data = {
            "song_id": self.song.id,
            "mood": self.mood.id,
            "note": "This song reminds me of rain.",
            "dedicated_to": "Someone"
        }

        response = self.client.post(
            "/memories/",
            data,
            format="json"
        )

        self.assertEqual(
            response.status_code,
            200
        )

        self.assertEqual(
            Memory.objects.count(),
            1
        )

        memory = Memory.objects.first()

        self.assertEqual(
            memory.user,
            self.user
        )

        self.assertEqual(
            memory.tenant,
            self.tenant
        )

    def test_unauthenticated_user_cannot_create_memory(self):

        data = {
        "song_id": self.song.id,
        "note": "Unauthorized attempt"
        }

        response = self.client.post(
        "/memories/",
        data,
        format="json"
        )

        self.assertEqual(
            response.status_code,
            401
        )

    def test_user_cannot_see_other_users_memories(self):

# SECOND TENANT
        tenant_b = Tenant.objects.create(
            name="Tenant B"
        )   

    # SECOND USER
        user_b = User.objects.create_user(
            username="user_b",
            password="pass123"
        )

        Profile.objects.create(
            user=user_b,
            tenant=tenant_b,
            role="user"
        )

        # MEMORY FOR USER B
        Memory.objects.create(
            user=user_b,
            tenant=tenant_b,
            song=self.song,
            note="Secret memory"
        )

        # LOGIN AS ORIGINAL USER
        self.client.force_authenticate(
            user=self.user
        )

        response = self.client.get("/memories/")

        self.assertEqual(
            response.status_code,
            200
        )

        self.assertEqual(
            len(response.data),
            0
        )