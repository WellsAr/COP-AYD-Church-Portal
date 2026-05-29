from datetime import date, datetime
import base64

from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string

from django.utils.timezone import now
from django.db.models import Count
from reportlab.pdfgen import canvas

from .forms import MemberForm
from .models import (
    Attendance,
    Member,
    ShepherdGroup,
    Session
)

from io import BytesIO
from django.http import FileResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import (
    SimpleDocTemplate,
    Spacer,
    Paragraph,
    Table,
    TableStyle,
)
from urllib.parse import urlencode
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from calendar import month_name

from reportlab.platypus import Image
from django.conf import settings
import os





# =====================================================
# ROLE HELPERS
# =====================================================

def get_user_role(user):

    if user.is_superuser:
        return 'superuser'

    if hasattr(user, 'profile'):
        return user.profile.role

    return None


def can_manage_members(user):

    if user.is_superuser:
        return True

    role = get_user_role(user)

    return role in [
        'pastor',
        'administrator',
        'elder',
        'overseer',
        'shepherd_leader'
    ]


def can_delete_members(user):

    role = get_user_role(user)

    return role in [
        'pastor',
        'administrator'
    ]


def get_accessible_members(user):

    role = get_user_role(user)

    # SUPERUSER / PASTOR
    if user.is_superuser or role == 'pastor':
        return Member.objects.filter(is_active=True)

    # ELDER -> session only
    elif role == 'elder':

        return Member.objects.filter(
            session=user.profile.session,
            is_active=True
        )

    # OVERSEER -> groups under them
    elif role == 'overseer':

        shepherds = user.profile.subordinates.filter(
            role='shepherd_leader'
        )

        groups = [
            shepherd.shepherd_group
            for shepherd in shepherds
            if shepherd.shepherd_group
        ]

        return Member.objects.filter(
            shepherd_group__in=groups,
            is_active=True
        )

    # SHEPHERD -> own group only
    elif role == 'shepherd_leader':

        return Member.objects.filter(
            shepherd_group=user.profile.shepherd_group,
            is_active=True
        )

    # ADMINISTRATOR
    elif role == 'administrator':

        return Member.objects.filter(is_active=True)

    return Member.objects.none()


# =====================================================
# LOGOUT
# =====================================================

@login_required
def logout_view(request):

    logout(request)

    response = redirect('login')

    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'

    return response


# =====================================================
# DASHBOARD
# =====================================================

@login_required
def dashboard(request):

    members = get_accessible_members(request.user)

    total_members = members.count()

    total_present_today = Attendance.objects.filter(
        member__in=members,
        date=date.today(),
        present=True
    ).count()

    context = {
        'active_page': 'dashboard',
        'total_members': total_members,
        'total_present_today': total_present_today
    }

    html = render_to_string(
        'members/partials/dashboard_content.html',
        context,
        request=request
    )

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return HttpResponse(html)

    return render(
        request,
        'members/dashboard.html',
        context
    )


# =====================================================
# REGISTER MEMBER
# =====================================================

@login_required
def register_member(request):

    if not can_manage_members(request.user):
        return redirect('dashboard')

    if request.method == 'POST':

        form = MemberForm(
            request.POST,
            request.FILES
        )

        if form.is_valid():

            member = form.save(commit=False)

            # TRACK WHO REGISTERED
            member.registered_by = request.user

            # CAMERA IMAGE
            captured_image = request.POST.get('captured_image')

            if captured_image:

                format, imgstr = captured_image.split(';base64,')

                ext = format.split('/')[-1]

                member.image = ContentFile(
                    base64.b64decode(imgstr),
                    name=f'captured.{ext}'
                )

            # ONLY SUPERUSER CAN UPLOAD FILES
            elif (
                request.FILES.get('image')
                and not request.user.is_superuser
            ):
                member.image = None

            # AUTO ASSIGN SHEPHERD GROUP
            birth_month = member.date_of_birth.month

            month_name = member.date_of_birth.strftime('%B')

            group, created = ShepherdGroup.objects.get_or_create(
                birth_month=birth_month,
                session=member.session,
                defaults={
                    'name': f'{month_name} Group'
                }
            )

            member.shepherd_group = group
            
            member.save()

            messages.success(
                request,
                'Member registered successfully.'
            )

            return redirect('member_list')

    else:
        form = MemberForm()

    context = {
        'form': form,
        'active_page': 'register'
    }

    html = render_to_string(
        'members/partials/register_content.html',
        context,
        request=request
    )

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return HttpResponse(html)

    return render(
        request,
        'members/register.html',
        context
    )


# =====================================================
# MEMBER LIST
# =====================================================

@login_required
def member_list(request):

    query = request.GET.get('q')

    members = get_accessible_members(request.user)

    if query:

        members = members.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(primary_phone__icontains=query) |
            Q(secondary_phone__icontains=query)
        )

    for member in members:

        last_attendance = Attendance.objects.filter(
            member=member,
            present=True
        ).order_by('-date').first()

        member.last_seen = (
            last_attendance.date
            if last_attendance
            else None
        )

    context = {
        'members': members,
        'query': query,
        'active_page': 'members'
    }

    html = render_to_string(
        'members/partials/member_list_content.html',
        context,
        request=request
    )

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return HttpResponse(html)

    return render(
        request,
        'members/member_list.html',
        context
    )


# =====================================================
# MEMBER DETAIL
# =====================================================

@login_required
def member_detail(request, member_id):

    members = get_accessible_members(request.user)

    member = get_object_or_404(
        members,
        id=member_id
    )

    attendance = Attendance.objects.filter(
        member=member
    ).order_by('-date')

    total_present = attendance.filter(
        present=True
    ).count()

    total_records = attendance.count()

    context = {
        'member': member,
        'attendance': attendance,
        'total_present': total_present,
        'total_records': total_records
    }

    html = render_to_string(
        'members/partials/member_detail_content.html',
        context,
        request=request
    )

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return HttpResponse(html)

    return render(
        request,
        'members/member_detail.html',
        context
    )


# =====================================================
# MARK ATTENDANCE
# =====================================================

@login_required
def mark_attendance(request):

    today = date.today()

    members = get_accessible_members(request.user)

    if request.method == 'POST':

        present_ids = request.POST.getlist('present[]')

        # REMOVE OLD RECORDS
        Attendance.objects.filter(
            member__in=members,
            date=today
        ).delete()

        # SAVE NEW RECORDS
        for member in members:

            Attendance.objects.create(
                member=member,
                date=today,
                present=str(member.id) in present_ids,
                marked_by=request.user
            )

        present_count = len(present_ids)

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':

            return JsonResponse({
                'success': True,
                'present': present_count,
                'total': members.count()
            })

        messages.success(
            request,
            'Attendance saved.'
        )

    attendance_records = {
        attendance.member.id: attendance.present
        for attendance in Attendance.objects.filter(
            member__in=members,
            date=today
        )
    }

    marked_count = Attendance.objects.filter(
        member__in=members,
        date=today,
        present=True
    ).count()

    unmarked_count = members.count() - marked_count

    context = {
        'members': members,
        'attendance_records': attendance_records,
        'today': today,
        'total': members.count(),
        'marked_count': marked_count,
        'unmarked_count': unmarked_count,
    }

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':

        return render(
            request,
            'members/partials/attendance_content.html',
            context
        )

    return render(
        request,
        'members/attendance.html',
        context
    )



# =====================================================
# REPORT
# =====================================================

@login_required
def attendance_report(request):
    user = request.user
    members = get_accessible_members(user)

    # FILTERS
    report_type = request.GET.get(
        'type',
        'monthly'
    )

    session_id = request.GET.get('session')

    group_id = request.GET.get('group')

    year = int(
        request.GET.get(
            'year',
            date.today().year
        )
    )

    month = int(
        request.GET.get(
            'month',
            date.today().month
        )
    )

    # SESSION FILTER
    if session_id:

        members = members.filter(
            session_id=session_id
        )

    # GROUP FILTER
    if group_id:

        members = members.filter(
            shepherd_group_id=group_id
        )

    # ATTENDANCE FILTER
    if report_type == 'monthly':

        attendance = Attendance.objects.filter(
            member__in=members,
            date__year=year,
            date__month=month
        )

    else:

        attendance = Attendance.objects.filter(
            member__in=members,
            date__year=year
        )

    report_data = []
    total_present_all = 0
    total_absent_all = 0

    for member in members:

        member_attendance = attendance.filter(
            member=member
        )

        total = member_attendance.count()

        present = member_attendance.filter(
            present=True
        ).count()

        absent = total - present

        rate = (
            round((present / total) * 100, 1)
            if total > 0 else 0
        )


        total_present_all += present
        total_absent_all += absent

        report_data.append({
            'member': member,
            'total': total,
            'present': present,
            'absent': absent,
            'rate': rate,
        })


    # OVERALL ATTENDANCE RATE
    overall_total = total_present_all + total_absent_all

    overall_rate = (
        round(
            (total_present_all / overall_total) * 100,
            1
        )
        if overall_total > 0 else 0
    )

    # AUTOMATED REPORT TITLE
    report_title = 'Full Church Attendance Report'

    if session_id:

        session = Session.objects.filter(
            id=session_id
        ).first()

        if session:
            report_title = (
                f'{session.get_name_display()} '
                'Session Attendance Report'
            )

    if group_id:

        group = ShepherdGroup.objects.filter(
            id=group_id
        ).first()

        if group:
            report_title = (
                f'{group.name} '
                'Attendance Report'
            )

    params = {
        "type": report_type,
        "year": year,
        "month": month,
    }

    if session_id:
        params["session"] = session_id

    if group_id:
        params["group"] = group_id

    pdf_url = "/reports/pdf/?" + urlencode(params)
    
    context = {
        'report_data': report_data,

        'report_type': report_type,
        'year': year,
        'month': month,

        'session_id': session_id,
        'group_id': group_id,

        'sessions': Session.objects.all(),
        'groups': ShepherdGroup.objects.all(),

        'report_title': report_title,

        'overall_rate': overall_rate,
        'total_present_all': total_present_all,
        'total_absent_all': total_absent_all,

        'generated_by': request.user.username,
        'generated_at': date.today(),
        
        "pdf_url": pdf_url
    }

    html = render_to_string(
        'members/partials/attendance_report_content.html',
        context,
        request=request
    )

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return HttpResponse(html)

    return render(
        request,
        'members/attendance_report.html',
        context
    )




@login_required
def attendance_report_pdf(request):
    user = request.user
    members = get_accessible_members(user)

    # =========================
    # FILTERS
    # =========================

    report_type = request.GET.get('type', 'monthly')
    year = int(request.GET.get('year', date.today().year))
    month = int(request.GET.get('month', date.today().month))

    attendance_qs = Attendance.objects.filter(member__in=members)

    if report_type == 'monthly':
        attendance_qs = attendance_qs.filter(date__year=year, date__month=month)
    else:
        attendance_qs = attendance_qs.filter(date__year=year)

    total_present = attendance_qs.filter(present=True).count()
    total_absent = attendance_qs.filter(present=False).count()
    total = total_present + total_absent

    overall_rate = round((total_present / total) * 100, 1) if total else 0

    # =========================
    # PREVIOUS
    # =========================

    prev_qs = Attendance.objects.filter(member__in=members)

    if report_type == 'monthly':
        prev_qs = prev_qs.filter(date__year=year, date__month=month-1 or 12)
    else:
        prev_qs = prev_qs.filter(date__year=year-1)

    prev_present = prev_qs.filter(present=True).count()
    prev_total = prev_qs.count()

    prev_rate = round((prev_present / prev_total) * 100, 1) if prev_total else 0
    diff = round(overall_rate - prev_rate, 1)

    # =========================
    # PDF SETUP
    # =========================

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        topMargin=80,
        bottomMargin=60
    )

    styles = getSampleStyleSheet()

    elements = []

    # =========================
    # PATHS
    # =========================

    logo_path = os.path.join(settings.BASE_DIR, 'members/static/members/imgs/church-logo.jpg')

    # =========================
    # HEADER + FOOTER + WATERMARK
    # =========================

    def draw_page(canvas, doc):
        width, height = letter

        # ---- WATERMARK (guaranteed visible) ----
        """if logo_path:
            canvas.saveState()
            canvas.translate(width/2, height/2)
            canvas.rotate(30)

            canvas.setFillGray(0.95)  # VERY light
            canvas.setFillAlpha(0.08) 
            
            canvas.drawImage(
                logo_path,
                -250, -150,
                width=600,
                height=700,
                preserveAspectRatio=True,
                mask='auto'
            )

            canvas.restoreState()"""

        # ---- HEADER ----
        canvas.saveState()

        if os.path.exists(logo_path):
            canvas.drawImage(logo_path, 40, height - 70, width=40, height=40)

        canvas.setFont("Helvetica-Bold", 14)
        canvas.drawString(90, height - 50, "COP-AYD Church")

        canvas.setFont("Helvetica", 10)
        canvas.drawString(90, height - 65, f"{report_type.title()} Attendance Report")
        
        canvas.line(40, height - 75, width - 40, height - 75)

        canvas.restoreState()

        # ---- FOOTER ----
        canvas.saveState()

        canvas.line(40, 50, width - 40, 50)

        canvas.setFont("Helvetica", 9)
        canvas.drawCentredString(width / 2, 35, f"Page {doc.page}")

        canvas.restoreState()

    # =========================
    # BODY
    # =========================

    elements.append(Spacer(1, 20))

    elements.append(Paragraph(
        f"<b>Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        styles['Normal']
    ))

    
    session_label = (
        f"{month_name[month]} {year}"
        if report_type == "monthly"
        else f"{year}"
    )

    elements.append(Paragraph(
        f"<b>Report Type:</b> {report_type.title()}",
        styles['Normal']
    ))

    elements.append(Paragraph(
        f"<b>Session:</b> {session_label}",
        styles['Normal']
    ))

    elements.append(Paragraph(
        f"<b>Generated By:</b> {user.get_full_name() or user.username}",
        styles['Normal']
    ))


    elements.append(Spacer(1, 15))

    # SUMMARY TABLE
    summary = Table([
        ["Metric", "Value"],
        ["Total Present", total_present],
        ["Total Absent", total_absent],
        ["Attendance Rate", f"{overall_rate}%"],
    ], colWidths=[250, 200])

    summary.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.3, colors.grey),
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
    ]))

    elements.append(summary)
    elements.append(Spacer(1, 25))

    # TREND TABLE
    trend = Table([
        ["Metric", "Value"],
        ["Current Rate", f"{overall_rate}%"],
        ["Previous Rate", f"{prev_rate}%"],
        ["Change", f"{diff}%"],
    ], colWidths=[250, 200])

    trend.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.3, colors.grey),
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
    ]))

    elements.append(trend)

    # =========================
    # BUILD
    # =========================

    doc.build(elements, onFirstPage=draw_page, onLaterPages=draw_page)

    buffer.seek(0)

    return FileResponse(
        buffer,
        as_attachment=False,
        filename="attendance_report.pdf"
    )










