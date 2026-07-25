from django.db import transaction
from django.contrib.auth import authenticate
from rest_framework import serializers
from jobs.models import *
        
class CandidateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Candidates
        fields = "__all__"
        read_only_fields = ["id", "user"]

        extra_kwargs = {
            "experience_level" : {
                "choices" : ['Intern', 'Entry level', 'Junior', 'Mid level', 'Senior', 'Lead', 'Expert'],
            } 
        }

class EmployerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employers
        fields = "__all__"
        read_only_fields = ["id", "user"]


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        trim_whitespace = False,
    )

    password_confirm = serializers.CharField(
        write_only=True,
        trim_whitespace = False,
    )

    company = serializers.PrimaryKeyRelatedField(
        queryset=Companies.objects.all(),
        required=False,
        allow_null=True,
        write_only=True,
    )

    class Meta:
        model = Users
        fields = ["id", "email", "phone_number", "role", "password", "password_confirm", "company"]
        read_only_fields = ["id"]

        extra_kwargs = {
            "email": {
                "required": True,
                "allow_blank": False,
            },
            "phone_number": {
                "required": True,
                "allow_blank": False,
                "allow_null": False,
            },
            "role": {
                "required": True,
                "choices" : ["Candidate", "Employer"]
            }, 
        }

    def validate_email(self, value):
        email = value.strip().lower()

        if Users.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError("User with this email already exists.")

        return email

    def validate_phone_number(self, value):
        phone_number = (
            value.replace(" ", "")
            .replace("-", "")
            .replace("(", "")
            .replace(")", "")
        )

        if phone_number.startswith("+"):
            digits = phone_number[1:]
        else:
            digits = phone_number

        if not digits.isdigit():
            raise serializers.ValidationError("Invalid phone number.")

        if Users.objects.filter(phone_number=phone_number).exists():
            raise serializers.ValidationError("User with this phone number already exists.")
        
        return phone_number

    def validate(self, attrs):
        if attrs.get("role") == "Employer" and attrs.get("company") is None:
            raise serializers.ValidationError("An employer must be assigned to a company.")
        
        if attrs.get("role") == "Candidate" and attrs.get("company") is not None:
            raise serializers.ValidationError({
                "company": "A candidate cannot be assigned to a company."
            })

        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError({"password_confirm": "Passwords do not match."})

        return attrs
    
    @transaction.atomic
    def create(self, validated_data):
        validated_data.pop("password_confirm")
        password = validated_data.pop("password")
        company = validated_data.pop("company", None)

        user = Users(**validated_data)
        user.set_password(password)
        user.save()

        if user.role == "Candidate":
            Candidates.objects.create(user=user)

        elif user.role == "Employer":
            Employers.objects.create(user=user, company=company)

        return user
    
class LoginSerializer(serializers.ModelSerializer):
    email = serializers.EmailField()
    password = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
    )

    class Meta:
        model = Users
        fields = ["email", "password"]

    def validate_email(self, value):
        return value.strip().lower()
    
    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")
        
        user = authenticate(request=self.context.get("request"), email=email, password=password)

        if user is None:
            raise serializers.ValidationError("Invalid email or password.")
        
        if not user.is_active:
            raise serializers.ValidationError("User account is inactive.")
        
        attrs["user"] = user

        return attrs

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
    )

    class Meta:
        model = Users
        fields = ["id", "password", "email", "phone_number", "role", "is_active", "last_login"]
        read_only_fields = [ "id", "role", "is_active", "last_login"]

        extra_kwargs = {
            "email": {
                "required": True,
                "allow_blank": False,
            },
            "phone_number": {
                "required": True,
                "allow_blank": False,
                "allow_null": False,
            }
        }

    def create(self, validated_data):
        password = validated_data.pop("password")

        user = Users(**validated_data)
        user.set_password(password)
        user.save()

        return user
    
    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)

        for field, value in validated_data.items():
            setattr(instance, field, value)

        if password:
            instance.set_password(password)

        instance.save()
        return instance

    def validate_email(self, value):
        email = value.strip().lower()
        queryset = Users.objects.filter(email__iexact=email)

        if self.instance is not None:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            raise serializers.ValidationError(
                "User with this email already exists."
            )

        return email
    
    def validate_phone_number(self, value):
        normalized = (
            value.replace(" ", "")
            .replace("-", "")
            .replace("(", "")
            .replace(")", "")
        )

        digits = normalized[1:] if normalized.startswith("+") else normalized

        if not digits.isdigit():
            raise serializers.ValidationError("Invalid phone number.")

        queryset = Users.objects.filter(phone_number=normalized)

        if self.instance is not None:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            raise serializers.ValidationError("User with this phone number already exists.")

        return normalized

class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Companies
        fields = "__all__"
        read_only_fields = ["id"]

class OfferSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobOffers
        fields = "__all__"
        read_only_fields = ["id", "company", "employer", "created_at"]

class ApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Applications
        fields = ["pk", "job_offer", "candidate", "cv", "status", "created_at", "updated_at"]
        read_only_fields = ["pk", "job_offer", "candidate", "status", "created_at"]

class StatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Applications
        fields = ["status"]

        extra_kwargs = {
            "status": {
                "required": True,
                "choices" : ['Sent', 'Reviewed', 'Rejected', 'Accepted']
            } 
        }

class CVSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cvs
        fields = ["id", "candidate", "file_url", "file_name", "created_at"]
        read_only_fields = ["id", "candidate", "created_at"]

    def validate_file_url(self, file):
        if file.content_type != "application/pdf":
            raise serializers.ValidationError("Only PDF files are allowed.")

        return file

