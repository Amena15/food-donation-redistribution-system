from .models import Profile

class UserFactory:
    @staticmethod
    def create_user(user, role):
        if role == 'donor':
            return Profile.objects.create(user=user, role='donor')
        elif role == 'recipient':
            return Profile.objects.create(user=user, role='recipient')
        elif role == 'admin':
            return Profile.objects.create(user=user, role='admin')
        else:
            raise ValueError(f"Unknown role: {role}")
