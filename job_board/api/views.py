from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from django.contrib.auth import login as django_login, logout
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status
from django.utils import timezone

from jobs.models import *
from .serializers import *
from .permissions import *
        
@api_view(["POST"])
@permission_classes([AllowAny])
def register_view(request):
    serializer = RegisterSerializer(data=request.data)

    if serializer.is_valid():
        user = serializer.save()
        return Response(
            {
                "message": "User registered successfully.",
                "user" : {
                    "id" : user.id,
                    "email" : user.email,
                    "phone_number" : user.phone_number,
                    "role" : user.role,
                },
            },
            status=status.HTTP_201_CREATED
        )
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    serializer = LoginSerializer(data=request.data, context={'request' : request})

    if serializer.is_valid():
        user = serializer.validated_data["user"]

        django_login(request, user)

        return Response(
            {
                "message" : "User logged in successfully.",
                "user" : {
                    "id" : user.id,
                    "email" : user.email,
                    "phone_number" : user.phone_number,
                    "role" : user.role,
                },
            },
            status=status.HTTP_200_OK
        )

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout_view(request):
    logout(request)
    return Response({"message": "User logged out successfully."}, status=status.HTTP_200_OK)

@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def user_profile(request):
    user = request.user

    if request.method == "GET":
        serializer = UserSerializer(user)
        return Response(serializer.data)
    
    if request.method == "PATCH":
        serializer = UserSerializer(user, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    if request.method == "DELETE":
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdmin])
def user_list(request):
    users = Users.objects.all()
    serializer = UserSerializer(users, many=True)

    return Response(serializer.data)

@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated, IsAdmin])
def user_profile_admin(request, user_id):
    user = Users.objects.filter(id=user_id).first()

    if user is None:
        return Response({'error' : 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == "GET":
        serializer = UserSerializer(user)
        return Response(serializer.data)
        
    if request.method == "PATCH":
        serializer = UserSerializer(user, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
           
    if request.method == "DELETE":
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated, IsCandidate])
def candidate_profile(request):
    user = request.user
    candidate = Candidates.objects.filter(user_id=user.id).first()

    if candidate is None:
        return Response({"error" : "Candidate profile not found."}, status=status.HTTP_404_NOT_FOUND)

    if request.method == "GET":
        serializer = CandidateSerializer(candidate)
        return Response(serializer.data)
    
    if request.method == "PATCH":
        serializer = CandidateSerializer(candidate, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def candidate_view(request, candidate_id):
    candidate = Candidates.objects.filter(id=candidate_id).first()

    if candidate is None:
        return Response({"error" : "Candidate profile not found."}, status=status.HTTP_404_NOT_FOUND)
    
    serializer = CandidateSerializer(candidate)
    return Response(serializer.data)
    
@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated, IsEmployer])
def employer_profile(request):
    user = request.user
    employer = Employers.objects.filter(user_id=user.id).first()

    if employer is None:
        return Response({"error" : "Employer profile not found."}, status=status.HTTP_404_NOT_FOUND)

    if request.method == "GET":
        serializer = EmployerSerializer(employer)
        return Response(serializer.data)
    
    if request.method == "PATCH":
        serializer = EmployerSerializer(employer, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def employer_view(request, employer_id):
    employer = Employers.objects.filter(id=employer_id).first()

    if employer is None:
        return Response({"error" : "Employer profile not found."}, status=status.HTTP_404_NOT_FOUND)

    serializer = EmployerSerializer(employer)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def company_list(request):
    companies = Companies.objects.all()
    serializer = CompanySerializer(companies, many=True)

    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def company_view(request, company_id):
    company = Companies.objects.filter(id=company_id).first()
    if company:
        serializer = CompanySerializer(company)
        return Response(serializer.data)
    
    return Response({"error" : "Company not found."}, status=status.HTTP_404_NOT_FOUND)

@api_view(['PATCH'])
@permission_classes([IsAuthenticated, IsEmployer | IsAdmin])
def company_view_patch(request, company_id):
    user = request.user
    company = Companies.objects.filter(id=company_id).first()

    if company is None:
        return Response({"error" : "Company does not exist."}, status=status.HTTP_404_NOT_FOUND)

    is_admin = request.user.is_staff or request.user.is_superuser

    if not is_admin:
        employer = Employers.objects.filter(user_id=user.id).first()

        if employer is None:
            return Response({"error": "Employer profile does not exist."}, status=status.HTTP_403_FORBIDDEN)

        if employer.company_id != company.id:
            return Response({"error": "You do not have permission to update this company."}, status=status.HTTP_403_FORBIDDEN)
    
    if request.method == "PATCH":
        if not is_admin and employer.company_id != company.id:
            return Response({"error" : "You do not have permission to update this company."}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = CompanySerializer(company, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
@api_view(['DELETE'])
@permission_classes([IsAuthenticated, IsAdmin])
def company_view_delete(request, company_id):
    company = Companies.objects.filter(id=company_id).first()

    if company is None:
        return Response({"error" : "Company does not exist."}, status=status.HTTP_404_NOT_FOUND)


    if request.method == 'DELETE':
        if company is None:
            return Response({"error" : "Company does not exist."}, status=status.HTTP_404_NOT_FOUND)

        company.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdmin])
def company_view_create(request):
    if request.method == 'POST':
        serializer = CompanySerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def company_job_offers(request, company_id):
    if not Companies.objects.filter(id=company_id).exists():
        return Response({"error": "Company does not exist."}, status=status.HTTP_404_NOT_FOUND)

    job_offers = JobOffers.objects.filter(company_id=company_id)
    serializer = OfferSerializer(job_offers, many=True)
    return Response(serializer.data)
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def company_employers(request, company_id):
    if not Companies.objects.filter(id=company_id).exists():
        return Response({"error": "Company does not exist."}, status=status.HTTP_404_NOT_FOUND)

    employers = Employers.objects.filter(company_id=company_id)
    serializer = EmployerSerializer(employers, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def offer_list(request):
    offers = JobOffers.objects.all()
    serializer = OfferSerializer(offers, many=True)

    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def offer_view(request, offer_id):
    offer = JobOffers.objects.filter(id=offer_id).first()
    
    if offer is None:
        return Response({"error" : "Offer does not exist."}, status=status.HTTP_404_NOT_FOUND)
    
    serializer = OfferSerializer(offer)
    return Response(serializer.data)

@api_view(['PATCH', 'DELETE'])
@permission_classes([IsAuthenticated, IsEmployer])
def offer_edit(request, offer_id):
    user = request.user
    offer = JobOffers.objects.filter(id=offer_id).first()
    employer = Employers.objects.get(user_id=user.id)
    
    if offer is None:
        return Response({"error" : "Offer does not exist."}, status=status.HTTP_404_NOT_FOUND)
    
    if offer.employer_id != employer.id:
        return Response({"error" : "You do not have permission to edit this job offer."}, status=status.HTTP_403_FORBIDDEN)

    if request.method == 'PATCH':
        serializer = OfferSerializer(offer, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    if request.method == 'DELETE':
        offer.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
@api_view(['POST'])
@permission_classes([IsAuthenticated, IsEmployer])
def offer_create(request):
    user = request.user
    serializer = OfferSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    employer = Employers.objects.filter(user_id=user.id).first()

    if employer is None or employer.company_id is None:
        return Response({"error": "Employer profile does not exist or employer is not assigned to a company."}, status=status.HTTP_403_FORBIDDEN)

    offer = serializer.save(employer=employer, company=employer.company)
    return Response(OfferSerializer(offer).data, status=status.HTTP_201_CREATED)

@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdmin])
def admin_offer_create(request, company_id, employer_id):
    serializer = OfferSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    employer = Employers.objects.filter(id=employer_id).first()
    if employer is None:
        return Response({"error": "Employer profile was not found."}, status=status.HTTP_404_NOT_FOUND)
    
    company = Companies.objects.filter(id=company_id).first()
    if company is None:
        return Response({"error": "Company was not found."}, status=status.HTTP_404_NOT_FOUND)
    
    if employer.company_id != company_id:
        return Response({"error": "Employer does not belong to the selected company."}, status=status.HTTP_400_BAD_REQUEST)
    
    offer = serializer.save(employer=employer, company=company)
    return Response(OfferSerializer(offer).data, status=status.HTTP_201_CREATED)

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsEmployer])
def employer_offers(request):
    user = request.user
    employer = Employers.objects.get(user_id=user.id)

    offers = JobOffers.objects.filter(employer_id=employer.id)
    serializer = OfferSerializer(offers, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsCandidate])
def candidate_applications(request):
    user = request.user
    candidate = Candidates.objects.get(user_id=user.id)

    applications = Applications.objects.filter(candidate_id=candidate.id)
    serializer = ApplicationSerializer(applications, many=True)

    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated, IsCandidate])
def application_create(request, offer_id):
    candidate = Candidates.objects.filter(user_id=request.user.id).first()
    offer = JobOffers.objects.filter(id=offer_id).first()

    if offer is None:
        return Response({"error" : "Offer was not found."}, status=status.HTTP_404_NOT_FOUND)
    
    cv_id = request.data.get("cv")
    cv = Cvs.objects.filter(id=cv_id, candidate=candidate).first()
    
    if cv is None:
        return Response({"error" : "CV was not found."}, status=status.HTTP_404_NOT_FOUND)

    if Applications.objects.filter(job_offer_id=offer_id, candidate_id=candidate.id, cv_id=cv_id).exists():
         return Response({"error" : "This application already exists."}, status=status.HTTP_409_CONFLICT)

    application = Applications.objects.create(
        job_offer=offer,
        candidate=candidate,
        cv=cv,
        status="Sent",
        created_at=timezone.now(),
        updated_at=timezone.now(),
    )

    return Response(ApplicationSerializer(application).data, status=status.HTTP_201_CREATED)

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsEmployer])
def employer_applications(request):
    user = request.user
    employer = Employers.objects.get(user_id=user.id)

    applications = Applications.objects.filter(job_offer__employer=employer)
    serializer = ApplicationSerializer(applications, many=True)

    return Response(serializer.data)

@api_view(['PATCH'])
@permission_classes([IsAuthenticated, IsEmployer])
def application_change_status(request, offer_id, candidate_id, cv_id):
    employer = Employers.objects.get(user=request.user)
    offer = JobOffers.objects.filter(id=offer_id).first()
    application = Applications.objects.filter(job_offer_id=offer_id, candidate_id=candidate_id, cv_id=cv_id).first()

    if offer is None:
        return Response({"error" : "Offer was not found."}, status=status.HTTP_404_NOT_FOUND) 

    if application is None:
        return Response({"error" : "Application was not found."}, status=status.HTTP_404_NOT_FOUND)
    
    if offer.employer_id != employer.id:
        return Response({"error" : "You do not have permission to edit this offer."}, status=status.HTTP_403_FORBIDDEN)
    
    serializer = StatusSerializer(application, data=request.data)

    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated, IsCandidate])
def cv_create(request):
    candidate = Candidates.objects.get(user_id=request.user.id)

    if request.method == "GET":
        cvs = Cvs.objects.filter(candidate=candidate).order_by("-created_at")

        serializer = CVSerializer(cvs, many=True, context={"request": request})

        return Response(serializer.data)
    
    if request.method == "POST":
        serializer = CVSerializer(data=request.data, context={"request": request})

        if serializer.is_valid():
            serializer.save(candidate=candidate)

            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
