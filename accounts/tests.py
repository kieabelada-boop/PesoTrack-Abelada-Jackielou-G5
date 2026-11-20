from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

CustomUser = get_user_model()


class AccountFlowTests(TestCase):
    def test_signup_shows_success_message_and_creates_user(self):
        """Account registration with validation and password hashing."""
        response = self.client.post(reverse("signup"), {
            "username": "aling_nena",
            "email": "alingnena@example.com",
            "first_name": "Nena",
            "last_name": "Santos",
            "business_name": "Aling Nena's Sari-Sari Store",
            "contact_number": "09171234567",
            "role": "RESELLER",
            "password1": "SecurePass123!",
            "password2": "SecurePass123!",
        }, follow=True)

        self.assertContains(response, "Your account has been created successfully")
        self.assertTemplateUsed(response, "registration/login.html")

        # Verify user exists in database and password is encrypted/hashed
        user = CustomUser.objects.get(username="aling_nena")
        self.assertEqual(user.email, "alingnena@example.com")
        self.assertEqual(user.business_name, "Aling Nena's Sari-Sari Store")
        self.assertEqual(user.role, "RESELLER")
        self.assertTrue(user.check_password("SecurePass123!"))
        self.assertNotEqual(user.password, "SecurePass123!")  # Must be hashed

    def test_signup_validation_rejects_duplicate_email(self):
        """Registration rejects duplicate email addresses."""
        CustomUser.objects.create_user(
            username="existing_user",
            email="duplicate@example.com",
            password="Password123!"
        )
        response = self.client.post(reverse("signup"), {
            "username": "new_user",
            "email": "duplicate@example.com",
            "first_name": "New",
            "last_name": "User",
            "business_name": "New Store",
            "contact_number": "09181234567",
            "role": "RESELLER",
            "password1": "Password123!",
            "password2": "Password123!",
        })
        self.assertFormError(response.context['form'], 'email', 'An account with this email address already exists.')

    def test_login_and_logout_flow(self):
        """User can log in with credentials and log out ending session."""
        user = CustomUser.objects.create_user(
            username="store_owner",
            email="owner@example.com",
            password="MySecretPassword123!",
            role="RESELLER"
        )

        # Invalid credentials rejected
        bad_login = self.client.post(reverse("login"), {
            "username": "store_owner",
            "password": "WrongPassword!"
        })
        self.assertEqual(bad_login.status_code, 200)
        self.assertContains(bad_login, "Please enter a correct username and password")

        # Valid login redirects to reseller dashboard
        good_login = self.client.post(reverse("login"), {
            "username": "store_owner",
            "password": "MySecretPassword123!"
        }, follow=True)
        self.assertRedirects(good_login, reverse("reseller_dashboard"))
        self.assertTrue(good_login.context['user'].is_authenticated)

        # Logout ends session
        logout_resp = self.client.post(reverse("logout"), follow=True)
        self.assertRedirects(logout_resp, reverse("login"))

    def test_admin_login_redirects_to_admin_dashboard(self):
        """Admin users are automatically redirected to admin dashboard upon login."""
        CustomUser.objects.create_user(
            username="sys_admin",
            email="sysadmin@example.com",
            password="AdminPassword123!",
            role="ADMIN"
        )
        response = self.client.post(reverse("login"), {
            "username": "sys_admin",
            "password": "AdminPassword123!"
        }, follow=True)
        self.assertRedirects(response, reverse("admin_dashboard"))

    def test_profile_update_changes_only_signed_in_user(self):
        """Logged-in users can update only their own profile details."""
        user = CustomUser.objects.create_user(
            username="reseller_user",
            password="Test-password-482!",
            email="user@example.com",
            business_name="Old Business Name",
            contact_number="09111111111"
        )
        other_user = CustomUser.objects.create_user(
            username="other_reseller",
            password="Test-password-482!",
            email="other@example.com",
            business_name="Other Business",
            contact_number="09222222222"
        )
        self.client.force_login(user)

        response = self.client.get(reverse("profile"))
        self.assertTemplateUsed(response, "registration/profile.html")

        update_response = self.client.post(reverse("profile"), {
            "username": "reseller_user",
            "email": "updated_email@example.com",
            "first_name": "UpdatedName",
            "last_name": "Santos",
            "business_name": "New Sari-Sari Store Name",
            "contact_number": "09999999999",
        }, follow=True)

        self.assertRedirects(update_response, reverse("profile"))
        user.refresh_from_db()
        other_user.refresh_from_db()

        self.assertEqual(user.first_name, "UpdatedName")
        self.assertEqual(user.business_name, "New Sari-Sari Store Name")
        self.assertEqual(user.contact_number, "09999999999")
        self.assertEqual(user.email, "updated_email@example.com")

        # Other user must remain untouched
        self.assertEqual(other_user.business_name, "Other Business")
        self.assertEqual(other_user.contact_number, "09222222222")

    def test_profile_requires_authentication(self):
        """Logged-out users cannot view or edit profiles."""
        response = self.client.get(reverse("profile"))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('profile')}")
