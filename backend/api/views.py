import pandas as pd

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from django.contrib.auth import authenticate, logout
from django.contrib.auth.models import User

from .models import Dataset, VehicleRecord


# -----------------------------------
# 1. USER REGISTRATION API (Class-Based + Token)
# -----------------------------------
@method_decorator(csrf_exempt, name='dispatch')
class RegisterUserView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return Response(
                {'error': 'Email and password required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if User.objects.filter(username=email).exists():
            return Response(
                {'error': 'Email already exists'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = User.objects.create_user(
            username=email,
            email=email,
            password=password
        )

        token, created = Token.objects.get_or_create(user=user)

        return Response(
            {
                'message': 'Registered successfully',
                'userId': user.id,
                'email': email,
                'token': token.key
            },
            status=status.HTTP_201_CREATED
        )


# -----------------------------------
# 2. USER LOGIN API (Class-Based + Token)
# -----------------------------------
@method_decorator(csrf_exempt, name='dispatch')
class LoginUserView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        user = authenticate(
            request,
            username=email,
            password=password
        )

        if user is not None:
            token, created = Token.objects.get_or_create(user=user)

            return Response({
                'message': 'Logged in successfully',
                'userId': user.id,
                'email': user.email,
                'token': token.key
            })

        return Response(
            {'error': 'Invalid credentials'},
            status=status.HTTP_401_UNAUTHORIZED
        )


# -----------------------------------
# 3. USER LOGOUT API
# -----------------------------------
@method_decorator(csrf_exempt, name='dispatch')
class LogoutUserView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response({
            'message': 'Logged out successfully'
        })


# -----------------------------------
# 4. GET CURRENT USER API
# -----------------------------------
@method_decorator(csrf_exempt, name='dispatch')
class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({
            'id': request.user.id,
            'email': request.user.email
        })


# -----------------------------------
# 5. DATASET LIST AND UPLOAD API
# -----------------------------------
@method_decorator(csrf_exempt, name='dispatch')
class DatasetListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        datasets = Dataset.objects.filter(
            user=request.user
        ).order_by('-created_at')

        data = [
            {
                'id': d.id,
                'filename': d.filename,
                'record_count': d.record_count,
                'status': d.status,
                'created_at': d.created_at
            }
            for d in datasets
        ]

        return Response(data)

    def post(self, request):
        file = request.FILES.get('file')

        if not file:
            return Response(
                {'error': 'No file uploaded'},
                status=status.HTTP_400_BAD_REQUEST
            )

        dataset = Dataset.objects.create(
            user=request.user,
            filename=file.name,
            status='processing'
        )

        try:
            df = pd.read_csv(file)

            required_columns = [
                'time',
                'vehicle_class',
                'x(px)',
                'y(px)'
            ]

            if not all(column in df.columns for column in required_columns):
                raise ValueError('Required CSV columns are missing.')

            records = []

            for _, row in df.iterrows():
                if pd.isna(row['time']) or pd.isna(row['vehicle_class']) or pd.isna(row['x(px)']) or pd.isna(row['y(px)']):
                    dataset.status = 'failed'
                    dataset.save()

                    return Response(
                        {'error': 'CSV validation failed. Missing values found.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                records.append(
                    VehicleRecord(
                        dataset=dataset,
                        time=str(row['time']),
                        vehicle_class=str(row['vehicle_class']),
                        x=float(row['x(px)']),
                        y=float(row['y(px)'])
                    )
                )

            VehicleRecord.objects.bulk_create(records)

            dataset.record_count = len(records)
            dataset.status = 'completed'
            dataset.save()

            return Response(
                {
                    'message': 'Imported successfully',
                    'datasetId': dataset.id,
                    'recordCount': len(records)
                },
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            dataset.status = 'failed'
            dataset.save()

            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


# -----------------------------------
# 6. DATASET DETAIL API
# -----------------------------------
@method_decorator(csrf_exempt, name='dispatch')
class DatasetDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, datasetId):
        try:
            ds = Dataset.objects.get(
                id=datasetId,
                user=request.user
            )

            return Response({
                'id': ds.id,
                'filename': ds.filename,
                'status': ds.status,
                'record_count': ds.record_count
            })

        except Dataset.DoesNotExist:
            return Response(
                {'error': 'Not found'},
                status=status.HTTP_404_NOT_FOUND
            )


# -----------------------------------
# 7. DATASET RECORDS API
# -----------------------------------
@method_decorator(csrf_exempt, name='dispatch')
class DatasetRecordsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, datasetId):
        try:
            ds = Dataset.objects.get(
                id=datasetId,
                user=request.user
            )
        except Dataset.DoesNotExist:
            return Response(
                {'error': 'Not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        records = VehicleRecord.objects.filter(dataset=ds)

        v_class = request.GET.get('vehicleClass')

        if v_class:
            records = records.filter(vehicle_class=v_class)

        try:
            page = max(1, int(request.GET.get('page', 1)))
            page_size = min(100, max(1, int(request.GET.get('pageSize', 10))))
        except ValueError:
            return Response(
                {'error': 'Invalid pagination parameters'},
                status=status.HTTP_400_BAD_REQUEST
            )

        total = records.count()

        start = (page - 1) * page_size
        end = start + page_size

        slice_records = records[start:end]

        data = [
            {
                'time': r.time,
                'vehicle_class': r.vehicle_class,
                'x(px)': r.x,
                'y(px)': r.y
            }
            for r in slice_records
        ]

        return Response({
            'total': total,
            'page': page,
            'pageSize': page_size,
            'records': data
        })


# -----------------------------------
# 8. DATASET STATISTICS API
# -----------------------------------
@method_decorator(csrf_exempt, name='dispatch')
class DatasetStatisticsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, datasetId):
        try:
            ds = Dataset.objects.get(
                id=datasetId,
                user=request.user
            )
        except Dataset.DoesNotExist:
            return Response(
                {'error': 'Not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        records = VehicleRecord.objects.filter(dataset=ds)

        v_class = request.GET.get('vehicleClass')

        if v_class:
            records = records.filter(vehicle_class=v_class)

        count = records.count()

        if count == 0:
            return Response({
                'count': 0,
                'x(px)': {'min': 0, 'median': 0, 'max': 0},
                'y(px)': {'min': 0, 'median': 0, 'max': 0}
            })

        xs = list(
            records.values_list('x', flat=True).order_by('x')
        )

        ys = list(
            records.values_list('y', flat=True).order_by('y')
        )

        def get_median(lst):
            n = len(lst)
            mid = n // 2

            if n % 2 != 0:
                return lst[mid]

            return (lst[mid - 1] + lst[mid]) / 2

        return Response({
            'count': count,
            'x(px)': {
                'min': xs[0],
                'median': get_median(xs),
                'max': xs[-1]
            },
            'y(px)': {
                'min': ys[0],
                'median': get_median(ys),
                'max': ys[-1]
            }
        })


# -----------------------------------
# 9. DATASET HISTOGRAM API
# -----------------------------------
@method_decorator(csrf_exempt, name='dispatch')
class DatasetHistogramView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, datasetId):
        try:
            ds = Dataset.objects.get(
                id=datasetId,
                user=request.user
            )
        except Dataset.DoesNotExist:
            return Response(
                {'error': 'Not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        records = VehicleRecord.objects.filter(dataset=ds)

        bins = {}

        for r in records:
            hour = r.time[:2] if len(r.time) >= 2 else '00'

            bins[hour] = bins.get(hour, 0) + 1

        result = [
            {
                'hour_bin': k,
                'count': v
            }
            for k, v in sorted(bins.items())
        ]

        return Response(result)


# -----------------------------------
# 10. DATASET STATUS API
# -----------------------------------
@method_decorator(csrf_exempt, name='dispatch')
class DatasetStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, datasetId):
        try:
            ds = Dataset.objects.get(
                id=datasetId,
                user=request.user
            )

            return Response({
                'id': ds.id,
                'status': ds.status,
                'record_count': ds.record_count
            })

        except Dataset.DoesNotExist:
            return Response(
                {'error': 'Not found'},
                status=status.HTTP_404_NOT_FOUND
            )