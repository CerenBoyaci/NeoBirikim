from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from .models import Consumption, Item
from django.contrib.auth.decorators import login_required
from .forms import UpdateUserForm
from .forms import ConsumptionForm
from .forms import IncomeForm, CustomIncomeForm
from .models import Income, IncomeType
from django.contrib.auth import update_session_auth_hash
import matplotlib.pyplot as plt
import io
import base64
from django.shortcuts import render
from .models import Income, Consumption
from django.contrib.auth.decorators import login_required



def about(request):
    return render(request, 'account/about.html')


def communication(request):
    return render(request, 'account/communication.html')

def user_login(request):
    next_page = request.GET.get('next', 'home')  # 'next' parametresi ile hedef sayfayı al

    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect(next_page)  # Login olduktan sonra 'next' parametresi ile gelen sayfaya yönlendir

        else:
            messages.error(request, "Kullanıcı adı veya şifre hatalı")

    return render(request, "account/login.html")




def user_register(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        if User.objects.filter(username=username).exists():
            messages.error(request, "Kullanıcı adı zaten kullanılıyor.")
        else:
            user = User.objects.create_user(username=username, password=password)
            user.save()
            messages.success(request, "Hesabınız başarıyla oluşturuldu")
            return redirect("user_login")
    return render(request, "account/register.html")



def user_logout(request):
    logout(request)
    return redirect("user_login")



def home(request):
    items=Item.objects.all()
    return render(request,"account/home.html",{"items":items})

@login_required
def update_user(request):
    if request.method == 'POST':
        form = UpdateUserForm(request.POST, instance=request.user)
        
        if form.is_valid():
            user = form.save()  # Kullanıcı bilgilerini güncelle
            
            # Eğer şifre değiştirildiyse, oturumun geçerli olmasını sağla
            if 'password' in form.changed_data:
                update_session_auth_hash(request, user)  # Şifre değişikliği sonrası oturum güncellemesi
                messages.success(request, "Şifreniz başarıyla güncellendi.")
            else:
                messages.success(request, "Kullanıcı bilgileri başarıyla güncellendi.")
            
            return redirect('home')  # Güncelleme sonrası ana sayfaya yönlendir
    else:
        form = UpdateUserForm(instance=request.user)  # Kullanıcının mevcut bilgileriyle formu doldur

    return render(request, 'account/update_user.html', {'form': form})


@login_required
def add_consumption(request):
    if request.method == 'POST':
        form = ConsumptionForm(request.POST)
        if form.is_valid():
            consumption = form.save(commit=False)
            consumption.user = request.user  # Tüketimi yapan kullanıcıyı kaydet
            
            # Girilmeyen alanları otomatik olarak 0 yap
            consumption.energy = form.cleaned_data.get('energy') or 0
            consumption.water = form.cleaned_data.get('water') or 0
            consumption.clothing = form.cleaned_data.get('clothing') or 0
            consumption.entertainment = form.cleaned_data.get('entertainment') or 0
            consumption.other_expenses = form.cleaned_data.get('other_expenses') or 0
            consumption.transportation = form.cleaned_data.get('transportation') or 0
            
            consumption.save()
            return redirect('success')  # Başarıyla kaydedildikten sonra 'success' sayfasına yönlendirin.
    else:
        form = ConsumptionForm()
    
    return render(request, 'account/add_consumption.html', {'form': form})

@login_required
def success_view(request):
    # Kullanıcının harcamalarını al
    consumptions = Consumption.objects.filter(user=request.user)

    return render(request, 'account/success.html', {'consumptions': consumptions})

from django.contrib import messages  # Mesajlar için

def add_income(request):
    income_form = IncomeForm()
    custom_income_form = CustomIncomeForm()

    # Toplam gelir hesaplama
    total_income = Income.objects.filter(user=request.user).aggregate(total=Sum('amount'))['total'] or 0

    # POST isteği olduğunda, form verilerini işliyoruz
    if request.method == 'POST':
        income_form = IncomeForm(request.POST)
        custom_income_form = CustomIncomeForm(request.POST)

        # Eğer standart gelir formu geçerliyse, geliri kaydediyoruz
        if income_form.is_valid():
            income = income_form.save(commit=False)
            income.user = request.user  # Gelir kaydeden kullanıcıyı ilişkilendiriyoruz
            income.save()

            messages.success(request, 'Gelir başarıyla kaydedildi!')

        # Eğer kullanıcı yeni bir gelir türü ekliyorsa, onu da kaydediyoruz
        if custom_income_form.is_valid():
            custom_type = custom_income_form.cleaned_data['custom_income_type']
            custom_amount = custom_income_form.cleaned_data['custom_amount']

            if custom_type and custom_amount:
                new_income_type, created = IncomeType.objects.get_or_create(name=custom_type)
                Income.objects.create(user=request.user, income_type=new_income_type, amount=custom_amount)

                messages.success(request, 'Yeni gelir türü başarıyla eklendi!')

    # Formları template'e gönderiyoruz
    return render(request, 'account/income.html', {
        'income_form': income_form,
        'custom_income_form': custom_income_form,
        'total_income': total_income  # Toplam geliri template'e ekliyoruz
    })


@login_required
def financial_summary(request):
    # Kullanıcının gelirlerini ve giderlerini alıyoruz
    incomes = Income.objects.filter(user=request.user)
    consumptions = Consumption.objects.filter(user=request.user)

    # Gelir türlerinin toplamlarını hesaplama
    income_types = {}
    for income in incomes:
        if income.income_type.name not in income_types:
            income_types[income.income_type.name] = 0
        income_types[income.income_type.name] += income.amount

    # Gider kategorilerinin toplamlarını hesaplama
    consumption_categories = {
        'Enerji': 0,
        'Su': 0,
        'Giyim': 0,
        'Eğlence': 0,
        'Diğer Giderler': 0,
        'Ulaşım': 0
    }

    for consumption in consumptions:
        consumption_categories['Enerji'] += consumption.energy
        consumption_categories['Su'] += consumption.water
        consumption_categories['Giyim'] += consumption.clothing
        consumption_categories['Eğlence'] += consumption.entertainment
        consumption_categories['Diğer Giderler'] += consumption.other_expenses
        consumption_categories['Ulaşım'] += consumption.transportation

    # Toplam gelir ve gider hesaplamaları
    total_income = sum(income_types.values())
    total_consumption = sum(consumption_categories.values())
    remaining_balance = total_income - total_consumption

    # Pasta grafiği oluşturmak için matplotlib kullanıyoruz
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 5))

    # Gelir dağılımı grafiği
    ax1.pie(income_types.values(), labels=income_types.keys(), autopct='%1.1f%%', startangle=90)
    ax1.set_title('Gelir Dağılımı')

    # Gider dağılımı grafiği
    ax2.pie(consumption_categories.values(), labels=consumption_categories.keys(), autopct='%1.1f%%', startangle=90)
    ax2.set_title('Gider Dağılımı')

    # Grafikleri image olarak dönüştürme
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    graph_image = base64.b64encode(buf.read()).decode('utf-8')

    return render(request, 'account/financial_summary.html', {
        'incomes': incomes,
        'consumptions': consumptions,
        'total_income': total_income,
        'total_consumption': total_consumption,
        'remaining_balance': remaining_balance,
        'graph_image': graph_image,
        'income_types': income_types,
        'consumption_categories': consumption_categories
    })
















from decimal import Decimal

@login_required
def compare(request):
    # Kullanıcının gelirlerini ve giderlerini al
    incomes = Income.objects.filter(user=request.user)
    consumptions = Consumption.objects.filter(user=request.user)

    # Gelir ve gider toplamlarını hesapla
    total_income = sum(income.amount for income in incomes)
    total_expenses = sum(
        consumption.energy +
        consumption.water +
        consumption.clothing +
        consumption.entertainment +
        consumption.other_expenses +
        consumption.transportation
        for consumption in consumptions
    )

    # Gider kategorileri ve toplamları
    categories = {
        'enerji': sum(consumption.energy for consumption in consumptions),
        'su': sum(consumption.water for consumption in consumptions),
        'giyim': sum(consumption.clothing for consumption in consumptions),
        'eğlence': sum(consumption.entertainment for consumption in consumptions),
        'diğer_giderler': sum(consumption.other_expenses for consumption in consumptions),
        'ulaşım': sum(consumption.transportation for consumption in consumptions),
    }

    # Tavsiye ve analiz mesajları
    recommendations = []
    if total_income > total_expenses:
        recommendations.append(f"Başarılı bir yönetim sergiliyorsunuz! Gelirleriniz giderlerinizden {total_income - total_expenses:.2f} TL fazla.")
    elif total_income < total_expenses:
        recommendations.append(f"Uyarı: Gelirleriniz giderlerinizi karşılamıyor. {total_expenses - total_income:.2f} TL açık vermişsiniz.")
    else:
        recommendations.append("Gelir ve giderleriniz dengeli. Ancak daha fazla tasarruf için fırsatlar bulunuyor.")

    # Gider kategorilerine yönelik öneriler
    for category, amount in categories.items():
        if amount > total_income * Decimal('0.3'):  # Gelirin %30'u kadar bir limit belirliyoruz
            excess = amount - (total_income * Decimal('0.3'))
            recommendations.append(
                f"Harcamalarınız ({category.capitalize()}) çok yüksek ({amount} TL). Bu kategoride ciddi tasarruf sağlanabilir. Harcamalarınızı {excess:.2f} TL kadar azaltmak, bütçenizi daha verimli hale getirecektir."
            )
        elif amount == 0:
            recommendations.append(f"{category.capitalize()} kategorisinde harcama yapmamışsınız. Eğer ihtiyaç varsa, bu kategoriyi gözden geçirmenizi öneririz.")
        else:
            recommendations.append(f"{category.capitalize()} harcamalarınız ({amount} TL) kabul edilebilir seviyede, ancak optimize edilebilecek alanlar var.")

    # Genel öneri
    recommendations.append("Daha fazla tasarruf etmek için gereksiz harcamaları sınırlamak ve harcamalarınızı kontrol altında tutmak önemli olacaktır.")

    # Kategorilerin toplam giderler içindeki oranı
    if total_expenses > 0:  # Toplam gider sıfır değilse oran hesapla
        for category, amount in categories.items():
            percentage = (amount / total_expenses) * 100
            if percentage > 50:
                recommendations.append(f"{category.capitalize()} harcamalarınız toplam giderlerinizin %{percentage:.2f}'ini oluşturuyor. Bu, oldukça yüksek bir oran ve bütçenizin dengelenmesi adına bu kategoriye odaklanmak iyi olacaktır.")
            elif percentage > 30:
                recommendations.append(f"{category.capitalize()} harcamalarınız toplam giderlerinizin %{percentage:.2f}'ini oluşturuyor. Harcamalarınızı optimize etmek ve bu kategoride tasarruf yapmak için adımlar atılabilir.")
            else:
                recommendations.append(f"{category.capitalize()} harcamalarınız toplam giderlerinizin %{percentage:.2f}'ini oluşturuyor. Dengeli bir harcama oranı sergiliyorsunuz.")
    else:
        recommendations.append("Hiç gider kaydı bulunamadı. Lütfen giderlerinizi kaydedin.")

    # Gelecekle ilgili tahminler
    if total_income > 0:  # Gelir sıfır değilse oranları hesapla
        expense_to_income_ratio = total_expenses / total_income  # Gelir-gider oranı
        future_incomes = [5000, 10000, 15000]  # Olası gelir senaryoları
        for future_income in future_incomes:
            future_expense = future_income * expense_to_income_ratio
            recommendations.append(
                f"Gelecekte geliriniz {future_income} TL olursa, mevcut harcama alışkanlıklarınıza göre yaklaşık {future_expense:.2f} TL harcama yapabilirsiniz. Bu durumda daha fazla birikim yapma potansiyeliniz artacak."
            )
            if future_expense < future_income:
                recommendations.append(
                    f"Bu durumda {future_income - future_expense:.2f} TL birikim yapma fırsatınız olacaktır. Bu fırsatı değerlendirmek, finansal hedeflerinize ulaşmanıza yardımcı olabilir."
                )
            else:
                recommendations.append(
                    f"Bu durumda harcamalarınız gelirlerinizi aşabilir, tasarruf yapmayı düşünmelisiniz. Gelecek için daha temkinli bir bütçe yönetimi önemlidir."
                )
    else:
        recommendations.append("Gelir veriniz bulunmadığından gelecekle ilgili tahmin yapılamıyor.")

    # Ekonomik tavsiyeler
    if total_income < total_expenses:
        deficit = total_expenses - total_income
        recommendations.append(f"Finansal dengede kalabilmek için {deficit:.2f} TL'lik bir bütçe açığınızı dengelemeniz gerekiyor.")
        for category, amount in categories.items():
            if amount > 0:
                reduction = min(deficit, amount * Decimal('0.2'))  # %20 tasarruf önerisi
                recommendations.append(
                    f"{category.capitalize()} harcamalarınızı {reduction:.2f} TL kadar azaltarak bütçe açığınızı dengelemeye yardımcı olabilirsiniz. Bu, finansal sağlığınız için kritik bir adım olacaktır."
                )
        recommendations.append("Bütçenizi dengelemek için tasarruf odaklı bir yaklaşım benimseyerek gelecekteki finansal istikrarınızı sağlamlaştırabilirsiniz.")
        recommendations.append("Ayrıca, her bir harcama kalemini gözden geçirerek gereksiz giderleri kısıtlamaya çalışın.")

    # Yatırım önerileri
    if total_income > total_expenses:
        recommendations.append("Artan gelirinizle birikim yapmaya başlayabilirsiniz. Uzun vadeli yatırım seçeneklerini araştırarak finansal hedeflerinize ulaşabilirsiniz.")
        recommendations.append("Düşük riskli yatırımlar (örneğin, devlet tahvilleri veya emlak) uzun vadede sabırlı bir şekilde yüksek getiri sağlayabilir.")

    return render(request, 'account/compare.html', {
        'total_income': total_income,
        'total_expenses': total_expenses,
        'categories': categories,
        'recommendations': recommendations
    })
























from django.shortcuts import render, redirect
from django.contrib import messages
from .models import SavingGoal, Saving
from .forms import SavingGoalForm, SavingForm
from django.db.models import Sum

def create_saving_goal(request):
    if request.method == 'POST':
        form = SavingGoalForm(request.POST)
        if form.is_valid():
            saving_goal = form.save(commit=False)
            saving_goal.user = request.user
            saving_goal.save()
            messages.success(request, "Hedefiniz başarıyla kaydedildi.")
            # Hedef oluşturulduktan sonra add_saving görünümüne yönlendir
            return redirect('add_saving', goal_id=saving_goal.id)
    else:
        form = SavingGoalForm()
    return render(request, 'account/create_saving_goal.html', {'form': form})

@login_required
def add_saving(request, goal_id):
    goal = get_object_or_404(SavingGoal, id=goal_id, user=request.user)

    # Toplam geliri hesapla
    total_income = Income.objects.filter(user=request.user).aggregate(total=Sum('amount'))['total'] or 0
    # Toplam birikimi hesapla
    total_savings = goal.savings.aggregate(total=Sum('amount'))['total'] or 0

    # Gelir - birikim kontrolü
    remaining_income = total_income - total_savings
    if remaining_income <= 0:
        messages.warning(request, "Geliriniz birikim yapmak için yeterli değil. Lütfen gelir ekleyin.")
        return redirect('income')  # Gelir sayfasına yönlendirme

    if total_savings >= goal.goal_amount:
        messages.warning(request, "Bu hedefe ulaştınız. Artık yeni birikim ekleyemezsiniz.")
        return redirect('saving_goal_list')

    if request.method == 'POST':
        form = SavingForm(request.POST)
        if form.is_valid():
            saving = form.save(commit=False)
            saving.goal = goal

            # Yeni birikim eklerken, gelirin 0'ın altına düşmemesi sağlanacak
            if remaining_income - saving.amount < 0:
                messages.warning(request, "Geliriniz birikim yapmaya yetmiyor.")
                return redirect('add_saving', goal_id=goal.id)

            saving.save()

            # Yeni toplam birikimi hesapla
            total_savings = goal.savings.aggregate(total=Sum('amount'))['total'] or 0

            if total_savings >= goal.goal_amount:
                messages.success(request, "Tebrikler! Hedefinize ulaştınız.")
            else:
                messages.success(request, "Birikiminiz başarıyla eklendi.")

            return redirect('saving_goal_list')
    else:
        form = SavingForm()

    return render(request, 'account/add_saving.html', {
        'form': form,
        'goal': goal,
        'remaining_income': remaining_income  # Kalan gelir bilgisi template'e ekleniyor
    })

from django.shortcuts import render
from django.db.models import Sum
from .models import SavingGoal, Income
from django.contrib.auth.decorators import login_required

@login_required
def saving_goal_list(request):
    goals = SavingGoal.objects.filter(user=request.user)
    goal_data = []
    
    # Toplam geliri hesapla
    total_income = Income.objects.filter(user=request.user).aggregate(total=Sum('amount'))['total'] or 0
    total_savings_all_goals = 0  # Bütün hedeflerin toplam birikimi için değişken

    for goal in goals:
        # Her hedef için toplam birikimi ve kalan tutarı hesapla
        total_savings = goal.savings.aggregate(total=Sum('amount'))['total'] or 0
        total_savings_all_goals += total_savings  # Bu hedefin birikimini toplam birikime ekle
        remaining_income = total_income - total_savings  # Kalan gelir

        # Hedefin ilerleme yüzdesi hesapla
        if goal.goal_amount > 0:
            progress = (total_savings / goal.goal_amount) * 100
        else:
            progress = 0  # Hedefin miktarı sıfırsa ilerleme 0 olur

        # Her hedefin birikimleri ile ilgili bilgileri ekle
        savings_data = goal.savings.all()  # Birikimlerin hepsi

        goal_data.append({
            'goal': goal,
            'total_savings': total_savings,
            'remaining': goal.goal_amount - total_savings,
            'remaining_income': remaining_income,
            'progress': progress,  # İlerleme yüzdesi
            'savings_data': savings_data,  # Birikimlerin tüm verileri
            'goal_created_at': goal.created_at  # Hedefin oluşturulma tarihi
        })
    
    # Pasta grafiği için veri
    chart_data = {
        'labels': ['Toplam Gelir', 'Toplam Birikim'],
        'datasets': [{
            'data': [total_income, total_savings_all_goals],
            'backgroundColor': ['#6e8efb', '#a777e3'],
        }]
    }
    
    return render(request, 'account/saving_goal_list.html', {
        'goal_data': goal_data, 
        'total_income': total_income,
        'total_savings_all_goals': total_savings_all_goals,  # Toplam birikim verisini template'e ekle
        'chart_data': chart_data,  # Pasta grafiği verisini ekle
    })


from decimal import Decimal
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Income, Consumption
import matplotlib.pyplot as plt
import io
import base64

@login_required
def environmental_recommendations(request):
    # Kullanıcının gelirlerini ve giderlerini al
    incomes = Income.objects.filter(user=request.user)
    consumptions = Consumption.objects.filter(user=request.user)

    # Gelir ve gider toplamlarını hesapla
    total_income = sum(income.amount for income in incomes)
    total_expenses = sum(
        consumption.energy +
        consumption.water +
        consumption.clothing +
        consumption.entertainment +
        consumption.other_expenses +
        consumption.transportation
        for consumption in consumptions
    )

    # Gider kategorileri ve toplamları
    categories = {
        'enerji': sum(consumption.energy for consumption in consumptions),
        'su': sum(consumption.water for consumption in consumptions),
        'giyim': sum(consumption.clothing for consumption in consumptions),
        'eğlence': sum(consumption.entertainment for consumption in consumptions),
        'diğer_giderler': sum(consumption.other_expenses for consumption in consumptions),
        'ulaşım': sum(consumption.transportation for consumption in consumptions),
    }

    # Tavsiye ve analiz mesajları
    recommendations = []
    if total_income > total_expenses:
        recommendations.append("Gelirleriniz giderlerinizi karşılıyor, tasarruf etmeye başlayabilirsiniz.")
    else:
        recommendations.append("Giderleriniz gelirlerinizi aşmakta, harcamalarınızı gözden geçirin.")

    if 0 <= categories['enerji'] <= 100:
        recommendations.append("Enerji harcamalarınız düşük seviyelerde. Bu seviyede enerji verimliliğinizi korumaya devam edin.")
    if 101 <= categories['enerji'] <= 200:
        recommendations.append("Enerji tüketiminiz biraz arttı, ancak hala düşük seviyelerde. Elektrikli cihazları gereksiz yere açık bırakmamaya özen gösterin.")
    if 201 <= categories['enerji'] <= 300:
        recommendations.append("Enerji harcamanız artıyor, bu doğaya zarar verebilir. Enerji verimli cihazlar kullanarak tasarruf sağlayabilirsiniz.")
    if 301 <= categories['enerji'] <= 400:
        recommendations.append("Enerji tüketiminiz çevre üzerinde daha fazla baskı yaratıyor. Isı yalıtımı yaparak ve enerji verimli cihazlar kullanarak tasarruf edebilirsiniz.")
    if 401 <= categories['enerji'] <= 500:
        recommendations.append("Enerji harcamanız çevre üzerinde olumsuz etkiler yaratıyor. Güneş enerjisi panelleri gibi yenilenebilir enerji kaynaklarına geçmeyi düşünebilirsiniz.")
    if 501 <= categories['enerji'] <= 600:
        recommendations.append("Enerji tüketiminiz yüksek seviyelere ulaşıyor. Bu seviyelerde daha sürdürülebilir alternatifler kullanmalısınız, örneğin akıllı termostatlar ve enerji verimli cihazlar.")
    if 601 <= categories['enerji'] <= 700:
        recommendations.append("Enerji tüketiminiz çevreye ciddi bir yük oluşturuyor. Evde enerji tasarruflu LED ışıklar kullanabilir ve gereksiz elektrikli cihazları kapatabilirsiniz.")
    if 701 <= categories['enerji'] <= 800:
        recommendations.append("Enerji harcamanız artıyor. Fosil yakıt tüketiminden kaçınmak için elektrikli araçları tercih edebilir ve toplu taşıma kullanabilirsiniz.")
    if 801 <= categories['enerji'] <= 900:
        recommendations.append("Yüksek enerji tüketiminiz doğaya ciddi zararlar veriyor. Güneş enerjisi sistemleri kurarak temiz enerji kullanabilirsiniz.")
    if 901 <= categories['enerji'] <= 1000:
        recommendations.append("Enerji tüketiminiz çok yüksek. Bu seviyede çevreye büyük zararlar vermemek için daha sürdürülebilir enerji çözümlerini tercih etmelisiniz.")
    if 1001 <= categories['enerji'] <= 1200:
        recommendations.append("Enerji harcamanız çevreyi tehdit ediyor. Isı pompaları ve yenilenebilir enerji sistemleri kullanarak daha temiz enerji kaynaklarına yönelebilirsiniz.")
    if 1201 <= categories['enerji'] <= 1400:
        recommendations.append("Enerji tüketiminiz fazla, doğaya ciddi zararlar veriyorsunuz. Bu seviyede enerji verimliliği sağlamak için evde daha verimli ısınma sistemleri kullanabilirsiniz.")
    if 1401 <= categories['enerji'] <= 1600:
        recommendations.append("Enerji harcamanız çevreye büyük zararlar veriyor. Akıllı cihazlar ve yenilenebilir enerji çözümleri ile tüketiminizi azaltabilirsiniz.")
    if 1601 <= categories['enerji'] <= 1800:
        recommendations.append("Enerji tüketiminiz doğaya ciddi şekilde zarar veriyor. Alternatif olarak, elektrikli araç kullanımı ve güneş enerjisi sistemleri gibi seçenekler önerilebilir.")
    if 1801 <= categories['enerji'] <= 2000:
        recommendations.append("Enerji harcamanız oldukça yüksek. Bu seviyede doğaya ciddi zararlar vermemek için sürdürülebilir enerji kaynaklarına geçiş yapmalısınız.")
    if 2001 <= categories['enerji'] <= 2500:
        recommendations.append("Enerji tüketiminiz çevre üzerinde büyük bir etki yaratıyor. Elektrikli araç kullanımı, daha verimli cihazlar ve yenilenebilir enerji sistemlerine geçiş yaparak doğayı koruyabilirsiniz.")
    if 2501 <= categories['enerji'] <= 3000:
        recommendations.append("Enerji harcamanız çok yüksek. Bu seviyede çevreyi korumak için daha fazla enerji verimli cihaz kullanabilir ve sürdürülebilir ulaşım seçeneklerini tercih edebilirsiniz.")
    if 3001 <= categories['enerji'] <= 3500:
        recommendations.append("Enerji tüketiminiz oldukça yüksek. Çevreyi korumak adına, evde enerji verimli cihazlar kullanabilir ve karbon ayak izinizi azaltabilirsiniz.")
    if 3501 <= categories['enerji'] <= 4000:
        recommendations.append("Enerji harcamanız doğaya ciddi zararlar veriyor. Bu seviyede çevreyi korumak için yenilenebilir enerji çözümleri ve enerji verimli cihazlar kullanmalısınız.")
    if 4001 <= categories['enerji'] <= 4500:
        recommendations.append("Enerji tüketiminiz çok fazla, çevreye ciddi zararlar veriyorsunuz. Yenilenebilir enerji kullanarak ve enerji verimli cihazlarla tüketiminizi azaltabilirsiniz.")
    if 4501 <= categories['enerji'] <= 5000:
        recommendations.append("Enerji tüketiminiz doğaya büyük zararlar veriyor. Bu seviyede daha fazla enerji verimliliği sağlamak için yeşil enerji çözümleri kullanmalısınız.")
    if 5001 <= categories['enerji'] <= 5500:
        recommendations.append("Enerji harcamanız çevre üzerinde büyük bir baskı yaratıyor. Fosil yakıtları terk edip, yenilenebilir enerji kaynaklarına yönelebilirsiniz.")
    if 5501 <= categories['enerji'] <= 6000:
        recommendations.append("Enerji tüketiminiz çok yüksek, doğaya ciddi zararlar veriyorsunuz. Güneş enerjisi gibi alternatif enerjilere geçiş yaparak çevreyi koruyabilirsiniz.")
    if 6001 <= categories['enerji'] <= 6500:
        recommendations.append("Enerji tüketiminiz doğaya ciddi şekilde zarar veriyor. Bu seviyede, enerji verimli cihazlar ve sürdürülebilir ulaşım yöntemleri kullanmalısınız.")
    if 6501 <= categories['enerji'] <= 7000:
        recommendations.append("Enerji harcamanız çevreyi büyük ölçüde etkiliyor. Yenilenebilir enerji sistemlerine geçmek, doğaya olan zararınızı azaltmanıza yardımcı olabilir.")
    if 7001 <= categories['enerji'] <= 7500:
        recommendations.append("Enerji tüketiminiz doğa üzerinde ciddi bir etki yaratıyor. Bu seviyede çevre dostu çözümler kullanarak tüketiminizi azaltabilirsiniz.")
    if 7501 <= categories['enerji'] <= 8000:
        recommendations.append("Enerji harcamanız oldukça yüksek. Çevreyi korumak için daha fazla enerji verimli cihaz kullanabilir ve doğa dostu ulaşım yöntemlerini tercih edebilirsiniz.")
    if 8001 <= categories['enerji'] <= 8500:
        recommendations.append("Enerji tüketiminiz çok fazla, çevreye büyük zararlar veriyorsunuz. Enerji tasarrufu sağlamak için sürdürülebilir enerji çözümleri kullanmalısınız.")
    if 8501 <= categories['enerji'] <= 9000:
        recommendations.append("Enerji tüketiminiz doğaya büyük bir tehdit oluşturuyor. Bu seviyede çevreyi korumak için yenilenebilir enerji kaynaklarına geçiş yapmalısınız.")
    if 9001 <= categories['enerji'] <= 9500:
        recommendations.append("Enerji harcamanız çok yüksek, doğaya ciddi zararlar veriyorsunuz. Güneş enerjisi sistemleri kurarak daha çevreci bir enerji kullanımı sağlayabilirsiniz.")
    if 9501 <= categories['enerji'] <= 10000:
        recommendations.append("Enerji tüketiminiz çevreyi tehdit ediyor. Bu seviyede yenilenebilir enerji çözümleri kullanarak doğaya zarar vermekten kaçınmalısınız.")
    if categories['enerji'] > 10000:
        recommendations.append("Enerji tüketiminiz son derece yüksek. Çevreye zarar vermemek için tamamen yenilenebilir enerji kaynaklarına geçiş yapmanızı öneriyoruz.")




    if 0 <= categories['su'] <= 50:
        recommendations.append("Su tüketiminiz çok düşük. Bu seviyede su tasarrufu sağlamanızı öneriyoruz.")
    if 51 <= categories['su'] <= 150:
        recommendations.append("Su tüketiminiz düşük seviyelerde. Su verimliliğinizi artırmak için su tasarruflu cihazlar kullanabilirsiniz.")
    if 151 <= categories['su'] <= 250:
        recommendations.append("Su tüketiminiz arttı. Su tasarrufu yapmak için duş sürelerinizi kısaltabilir ve su verimli cihazlar kullanabilirsiniz.")
    if 251 <= categories['su'] <= 350:
        recommendations.append("Su tüketiminiz yükseliyor. Su tasarrufu sağlamak için daha az su kullanabilir ve sızdırmaz musluklar kullanabilirsiniz.")
    if 351 <= categories['su'] <= 450:
        recommendations.append("Su tüketiminiz arttı. Daha dikkatli olmalı ve suyu boşa harcamamaya özen göstermelisiniz.")
    if 451 <= categories['su'] <= 550:
        recommendations.append("Su tüketiminiz yüksek seviyelerde. Su tasarrufu yapmak için su verimli cihazları kullanmayı tercih edebilirsiniz.")
    if 551 <= categories['su'] <= 650:
        recommendations.append("Su tüketiminiz oldukça yüksek. Su kullanımınızı azaltmak için duş sürelerinizi kısaltabilir ve su tasarruflu cihazlar tercih edebilirsiniz.")
    if 651 <= categories['su'] <= 750:
        recommendations.append("Su tüketiminiz çevre üzerinde daha fazla baskı yaratıyor. Suyu daha verimli kullanmalısınız.")
    if 751 <= categories['su'] <= 850:
        recommendations.append("Su tüketiminiz çevreyi olumsuz etkiliyor. Su tasarrufu sağlamak için çamaşır ve bulaşık makinelerini tam kapasite çalıştırabilirsiniz.")
    if 851 <= categories['su'] <= 950:
        recommendations.append("Su harcamanız fazla. Suyu daha dikkatli kullanarak çevreyi koruyabilirsiniz.")
    if 951 <= categories['su'] <= 1050:
        recommendations.append("Su tüketiminiz oldukça yüksek. Suyunuzu verimli kullanmak için bahçenizi su kaynaklarını dikkate alarak sulayabilirsiniz.")
    if 1051 <= categories['su'] <= 1150:
        recommendations.append("Su tüketiminiz çevre üzerinde büyük bir baskı oluşturuyor. Suyu tasarruflu kullanarak bu baskıyı azaltabilirsiniz.")
    if 1151 <= categories['su'] <= 1250:
        recommendations.append("Su tüketiminiz oldukça fazla. Bu seviyelerde su tasarrufu yapmaya özen göstermelisiniz.")
    if 1251 <= categories['su'] <= 1350:
        recommendations.append("Su tüketiminiz doğa üzerinde büyük bir etki yaratıyor. Su tasarrufu sağlamak için damla sulama gibi yöntemler kullanabilirsiniz.")
    if 1351 <= categories['su'] <= 1450:
        recommendations.append("Su harcamanız çevre üzerinde ciddi bir yük oluşturuyor. Bu seviyelerde suyu daha verimli kullanmak önemlidir.")
    if 1451 <= categories['su'] <= 1550:
        recommendations.append("Su tüketiminiz çok yüksek. Suyu daha verimli kullanarak çevreyi koruyabilirsiniz.")
    if 1551 <= categories['su'] <= 1650:
        recommendations.append("Su harcamanız artmaya devam ediyor. Bu seviyelerde su verimli cihazlar ve su tasarrufu önlemleri almanız gerekebilir.")
    if 1651 <= categories['su'] <= 1750:
        recommendations.append("Su tüketiminiz çevre üzerinde büyük etkiler yaratıyor. Su kullanımını azaltarak çevreyi koruyabilirsiniz.")
    if 1751 <= categories['su'] <= 1850:
        recommendations.append("Su harcamanız çevreyi tehdit ediyor. Bu seviyede su tasarrufu yapmak için daha etkili yöntemler uygulamalısınız.")
    if 1851 <= categories['su'] <= 1950:
        recommendations.append("Su tüketiminiz çok yüksek. Bu seviyede su kullanımınızı azaltarak çevreyi korumanız gerekmektedir.")
    if 1951 <= categories['su'] <= 2050:
        recommendations.append("Su tüketiminiz oldukça fazla. Bu seviyede suyu daha dikkatli kullanmalı ve su tasarruflu cihazlar kullanmalısınız.")
    if 2051 <= categories['su'] <= 2150:
        recommendations.append("Su harcamanız çevreyi büyük ölçüde etkiliyor. Bu seviyelerde su verimli cihazlar kullanarak suyu daha verimli kullanabilirsiniz.")
    if 2151 <= categories['su'] <= 2250:
        recommendations.append("Su tüketiminiz çevreye ciddi bir zarar veriyor. Suyu verimli kullanarak bu etkiyi azaltabilirsiniz.")
    if 2251 <= categories['su'] <= 2350:
        recommendations.append("Su harcamanız çevreye büyük zararlar veriyor. Su tasarrufu için daha etkili yöntemler kullanmanız gerekebilir.")
    if 2351 <= categories['su'] <= 2450:
        recommendations.append("Su tüketiminiz son derece yüksek. Bu seviyelerde su kullanımınızı daha verimli hale getirebilirsiniz.")
    if 2451 <= categories['su'] <= 2550:
        recommendations.append("Su tüketiminiz doğaya büyük zararlar veriyor. Suyu daha dikkatli kullanarak çevreyi koruyabilirsiniz.")
    if 2551 <= categories['su'] <= 2650:
        recommendations.append("Su tüketiminiz çevreyi ciddi şekilde etkiliyor. Su tasarrufu sağlamak için daha etkili çözümler kullanmalısınız.")
    if 2651 <= categories['su'] <= 2750:
        recommendations.append("Su harcamanız çevre üzerinde çok büyük etkiler yaratıyor. Su verimli cihazlar kullanarak çevreyi koruyabilirsiniz.")
    if 2751 <= categories['su'] <= 2850:
        recommendations.append("Su tüketiminiz çok yüksek. Bu seviyede suyu verimli kullanmak çevreyi korumaya yardımcı olacaktır.")
    if 2851 <= categories['su'] <= 2950:
        recommendations.append("Su tüketiminiz çevreye büyük zarar veriyor. Suyu daha verimli kullanarak bu durumu düzeltebilirsiniz.")
    if 2951 <= categories['su'] <= 3000:
        recommendations.append("Su harcamanız son derece yüksek. Bu seviyede çevreyi korumak için su tasarrufu yapmanız önemlidir.")
    if categories['su'] > 3000:
        recommendations.append("Su tüketimini azaltarak su faturalarınızı düşürebilirsiniz.")
    
    

    if 0 <= categories['giyim'] <= 200:
        recommendations.append("Giyim alışverişlerinizi daha dikkatli planlayarak tasarruf sağlayabilirsiniz.")
    if 201 <= categories['giyim'] <= 300:
        recommendations.append("Giyim harcamalarınız artıyor. Daha az alışveriş yaparak tasarruf edebilirsiniz.")
    if 301 <= categories['giyim'] <= 400:
        recommendations.append("Giyim harcamalarınız yüksek seviyelerde. Giyim alışverişlerinizi daha iyi planlayabilirsiniz.")
    if 401 <= categories['giyim'] <= 500:
        recommendations.append("Giyim harcamalarınız yükseliyor. İndirim dönemlerini takip ederek tasarruf edebilirsiniz.")
    if 501 <= categories['giyim'] <= 600:
        recommendations.append("Giyim harcamalarınız fazla. Daha fazla tasarruf etmek için gereksiz alışverişlerden kaçınabilirsiniz.")
    if 601 <= categories['giyim'] <= 700:
        recommendations.append("Giyim harcamalarınız oldukça yüksek. İhtiyacınız olmayan ürünlerden kaçınmalısınız.")
    if 701 <= categories['giyim'] <= 800:
        recommendations.append("Giyim harcamalarınız çok yüksek. Daha az alışveriş yaparak bütçenizi koruyabilirsiniz.")
    if 801 <= categories['giyim'] <= 900:
        recommendations.append("Giyim harcamalarınız bütçenizi zorlayabilir. Planlı alışveriş yaparak tasarruf edebilirsiniz.")
    if 901 <= categories['giyim'] <= 1000:
        recommendations.append("Giyim harcamalarınız kontrol dışına çıkabilir. Alışveriş öncesinde ihtiyaç listesi hazırlayabilirsiniz.")
    if 1001 <= categories['giyim'] <= 1100:
        recommendations.append("Giyim harcamalarınız aşırı artmış durumda. İhtiyaç dışı ürünlerden kaçınarak tasarruf yapabilirsiniz.")
    if 1101 <= categories['giyim'] <= 1200:
        recommendations.append("Giyim harcamalarınız oldukça yüksek. Daha bilinçli tüketim yapmanız gerekebilir.")
    if 1201 <= categories['giyim'] <= 1300:
        recommendations.append("Giyim alışverişleriniz bütçenize zarar verebilir. Harcamalarınızı yeniden gözden geçirin.")
    if 1301 <= categories['giyim'] <= 1400:
        recommendations.append("Giyim harcamalarınız doğrudan bütçenize yük bindiriyor. Daha az alışveriş yapmayı deneyin.")
    if 1401 <= categories['giyim'] <= 1500:
        recommendations.append("Giyim harcamalarınız oldukça yüksek seviyelerde. İndirim dönemlerini ve ikinci el pazarlarını değerlendirebilirsiniz.")
    if 1501 <= categories['giyim'] <= 1600:
        recommendations.append("Giyim alışverişleriniz bütçenizi sarsabilir. Daha bilinçli alışveriş yapmaya çalışın.")
    if 1601 <= categories['giyim'] <= 1700:
        recommendations.append("Giyim harcamalarınız çok fazla. Daha sürdürülebilir bir alışveriş yaklaşımını benimseyebilirsiniz.")
    if 1701 <= categories['giyim'] <= 1800:
        recommendations.append("Giyim alışverişleriniz yüksek seviyelerde. Tasarruf için ikinci el ürünleri düşünebilirsiniz.")
    if 1801 <= categories['giyim'] <= 1900:
        recommendations.append("Giyim harcamalarınız artmaya devam ediyor. İhtiyacınız olan ürünleri satın almaya odaklanın.")
    if 1901 <= categories['giyim'] <= 2000:
        recommendations.append("Giyim alışverişleriniz bütçenizi zorlayabilir. İhtiyaç listenizi gözden geçirin ve tasarruf yapmayı hedefleyin.")
    if 2001 <= categories['giyim'] <= 3000:
        recommendations.append("Giyim harcamalarınız kritik seviyelere ulaşmış durumda. İhtiyacınız olmayan ürünlerden uzak durmalısınız.")
    if 3001 <= categories['giyim'] <= 4000:
        recommendations.append("Giyim harcamalarınız aşırı yüksek. Alışveriş alışkanlıklarınızı gözden geçirmeniz gerekiyor.")
    if 4001 <= categories['giyim'] <= 5000:
        recommendations.append("Giyim harcamalarınız sürdürülebilir olmaktan çıktı. Daha bilinçli ve tasarruflu bir yaklaşım benimsemelisiniz.")
    if categories['giyim'] > 5000:
        recommendations.append("Giyim alışverişleriniz artık doğaya da ekonominize de zarar verecek durumda. Daha dikkatli planlayarak tasarruf sağlayabilirsiniz.")
    
    
    
    if 0 <= categories['eğlence'] <= 100:
        recommendations.append("Eğlence harcamalarınızı çevre dostu etkinliklere yönelterek doğaya katkı sağlayabilirsiniz.")
    if 101 <= categories['eğlence'] <= 200:
        recommendations.append("Doğa yürüyüşleri veya topluluk temizlik etkinlikleri gibi ekonomik ve çevreci aktiviteleri deneyebilirsiniz.")
    if 201 <= categories['eğlence'] <= 300:
        recommendations.append("Eğlence harcamalarınızı azaltarak çevreye daha az zarar veren etkinliklere öncelik verebilirsiniz.")
    if 301 <= categories['eğlence'] <= 400:
        recommendations.append("Geri dönüşüm temalı etkinlikler veya enerji dostu eğlence seçeneklerini değerlendirin.")
    if 401 <= categories['eğlence'] <= 500:
        recommendations.append("Eğlence harcamalarınızda çevre bilincini artıracak etkinlikler tercih ederek bütçenizi ve doğayı koruyabilirsiniz.")
    if 501 <= categories['eğlence'] <= 600:
        recommendations.append("Eğlence harcamalarınız artıyor. Daha az enerji tüketen eğlenceli aktiviteler seçmeye çalışın.")
    if 601 <= categories['eğlence'] <= 700:
        recommendations.append("Daha sürdürülebilir eğlence seçeneklerine yönelerek hem doğayı hem de bütçenizi koruyabilirsiniz.")
    if 701 <= categories['eğlence'] <= 800:
        recommendations.append("Toplum odaklı ve çevre dostu etkinliklere katılarak harcamalarınızı azaltabilirsiniz.")
    if 801 <= categories['eğlence'] <= 900:
        recommendations.append("Eğlence bütçenizi çevreye duyarlı etkinlikler için planlamayı düşünebilirsiniz.")
    if 901 <= categories['eğlence'] <= 1000:
        recommendations.append("Daha çevreci bir yaşam için harcamalarınızı doğa dostu aktivitelerle dengeleyebilirsiniz.")
    if 1001 <= categories['eğlence'] <= 1100:
        recommendations.append("Eğlence harcamalarınız yüksek. Gönüllü çevre çalışmaları gibi maliyetsiz etkinlikler değerlendirin.")
    if 1101 <= categories['eğlence'] <= 1200:
        recommendations.append("Eğlence bütçenizi doğal alanları korumaya yönelik etkinlikler için kullanmayı düşünebilirsiniz.")
    if 1201 <= categories['eğlence'] <= 1300:
        recommendations.append("Çevre bilincinizi artıracak ekonomik eğlence seçeneklerini tercih edebilirsiniz.")
    if 1301 <= categories['eğlence'] <= 1400:
        recommendations.append("Eğlence harcamalarınızı azaltarak daha çevre dostu bir yaşam tarzını benimseyebilirsiniz.")
    if 1401 <= categories['eğlence'] <= 1500:
        recommendations.append("Doğa koruma odaklı etkinliklere katılarak hem eğlenebilir hem de çevreye katkı sağlayabilirsiniz.")
    if 1501 <= categories['eğlence'] <= 1600:
        recommendations.append("Eğlence bütçenizi enerji tasarrufu sağlayan aktivitelerle dengelemeye çalışabilirsiniz.")
    if 1601 <= categories['eğlence'] <= 1700:
        recommendations.append("Çevre dostu eğlence seçenekleriyle hem doğayı hem de bütçenizi koruyabilirsiniz.")
    if 1701 <= categories['eğlence'] <= 1800:
        recommendations.append("Eğlence harcamalarınızı azaltıp çevre koruma etkinliklerine yönelerek faydalı bir katkı sağlayabilirsiniz.")
    if 1801 <= categories['eğlence'] <= 1900:
        recommendations.append("Doğayı koruma bilinciyle daha uygun maliyetli eğlence aktivitelerine odaklanabilirsiniz.")
    if 1901 <= categories['eğlence'] <= 2000:
        recommendations.append("Eğlence bütçenizi düşürüp çevre dostu yaşam alışkanlıkları geliştirebilirsiniz.")
    if 2001 <= categories['eğlence'] <= 3000:
        recommendations.append("Eğlence harcamalarınızı çevreyi destekleyen aktivitelerle birleştirerek denge sağlayabilirsiniz.")
    if 3001 <= categories['eğlence'] <= 4000:
        recommendations.append("Eğlence giderlerinizi doğa koruma projelerine katılarak optimize etmeyi düşünebilirsiniz.")
    if 4001 <= categories['eğlence'] <= 5000:
        recommendations.append("Eğlence harcamalarınızı doğa dostu alternatiflerle değiştirerek sürdürülebilir bir yaşam tarzını destekleyebilirsiniz.")
    if categories['eğlence'] > 5000:
        recommendations.append("Eğlence harcamalarınızı kontrol altına alarak bütçenizi dengeleyebilirsiniz.")

    
    if 0 <= categories['ulaşım'] <= 80:
        recommendations.append("Ulaşım harcamalarınızı toplu taşıma kullanarak azaltabilirsiniz.")
    if 81 <= categories['ulaşım'] <= 160:
        recommendations.append("Daha sık toplu taşıma kullanarak hem bütçenizi hem de çevreyi koruyabilirsiniz.")
    if 161 <= categories['ulaşım'] <= 240:
        recommendations.append("Kısa mesafelerde yürüyüş veya bisiklet gibi çevreci ulaşım alternatiflerini deneyebilirsiniz.")
    if 241 <= categories['ulaşım'] <= 320:
        recommendations.append("Araç paylaşımı gibi yöntemlerle hem maliyetleri düşürebilir hem de karbon ayak izinizi azaltabilirsiniz.")
    if 321 <= categories['ulaşım'] <= 400:
        recommendations.append("Elektrikli scooter veya bisiklet gibi enerji dostu ulaşım araçlarını tercih edebilirsiniz.")
    if 401 <= categories['ulaşım'] <= 480:
        recommendations.append("Toplu taşıma kartları veya abonelikler ile ulaşım maliyetlerinizi daha ekonomik hale getirebilirsiniz.")
    if 481 <= categories['ulaşım'] <= 560:
        recommendations.append("Araç kullanımınızı azaltarak hem çevreye hem de bütçenize katkıda bulunabilirsiniz.")
    if 561 <= categories['ulaşım'] <= 640:
        recommendations.append("Ulaşım harcamalarınız yüksek görünüyor. Daha çevreci seçenekleri değerlendirebilirsiniz.")
    if 641 <= categories['ulaşım'] <= 720:
        recommendations.append("Yürüyüş yaparak hem sağlığınıza hem de çevreye katkı sağlayabilirsiniz.")
    if 721 <= categories['ulaşım'] <= 800:
        recommendations.append("Araba yerine toplu taşıma veya araç paylaşımı kullanarak karbon salınımınızı azaltabilirsiniz.")
    if 801 <= categories['ulaşım'] <= 880:
        recommendations.append("Ulaşım bütçeniz artıyor. Daha sürdürülebilir ve ekonomik seçeneklere yönelebilirsiniz.")
    if 881 <= categories['ulaşım'] <= 960:
        recommendations.append("Kendi aracınız yerine çevreci ulaşım yöntemlerini kullanarak tasarruf edebilirsiniz.")
    if 961 <= categories['ulaşım'] <= 1040:
        recommendations.append("Daha çevreci ulaşım araçlarını tercih ederek çevreye olan etkinizi azaltabilirsiniz.")
    if 1041 <= categories['ulaşım'] <= 1120:
        recommendations.append("Araba yerine bisiklet veya scooter gibi düşük maliyetli ve çevreci alternatiflere yönelebilirsiniz.")
    if 1121 <= categories['ulaşım'] <= 1200:
        recommendations.append("Ulaşım harcamalarınız fazla yüksek. Çevre dostu toplu taşıma seçeneklerini tercih etmeyi düşünebilirsiniz.")
    if 1201 <= categories['ulaşım'] <= 1280:
        recommendations.append("Araç paylaşımı kullanarak çevreye katkıda bulunabilir ve maliyetlerinizi azaltabilirsiniz.")
    if 1281 <= categories['ulaşım'] <= 1360:
        recommendations.append("Elektrikli araçlar veya hibrit araçlar gibi çevre dostu seçenekleri değerlendirebilirsiniz.")
    if 1361 <= categories['ulaşım'] <= 1440:
        recommendations.append("Daha az fosil yakıt kullanan ulaşım yöntemlerini tercih ederek sürdürülebilir bir yaşam tarzı benimseyebilirsiniz.")
    if 1441 <= categories['ulaşım'] <= 1520:
        recommendations.append("Ulaşım giderlerinizi azaltmak için seyahatlerinizi planlı yapmayı deneyebilirsiniz.")
    if 1521 <= categories['ulaşım'] <= 1600:
        recommendations.append("Çevre dostu araç kiralama hizmetlerini değerlendirerek karbon ayak izinizi azaltabilirsiniz.")
    if 1601 <= categories['ulaşım'] <= 1680:
        recommendations.append("Ulaşım harcamalarınızı azaltmak için düzenli toplu taşıma kullanımını alışkanlık haline getirin.")
    if 1681 <= categories['ulaşım'] <= 1760:
        recommendations.append("Daha çevreci ulaşım alternatiflerine yönelerek harcamalarınızı kontrol altında tutabilirsiniz.")
    if 1761 <= categories['ulaşım'] <= 1840:
        recommendations.append("Karbon ayak izinizi azaltmak için elektrikli araç veya toplu taşıma kullanabilirsiniz.")
    if 1841 <= categories['ulaşım'] <= 1920:
        recommendations.append("Ulaşım giderlerinizi sürdürülebilir alternatiflerle dengelemeyi düşünebilirsiniz.")
    if 1921 <= categories['ulaşım'] <= 2000:
        recommendations.append("Fosil yakıt kullanımınızı azaltarak doğaya katkıda bulunabilirsiniz.")
    if 2001 <= categories['ulaşım'] <= 3000:
        recommendations.append("Ulaşım giderleriniz oldukça yüksek. Daha çevreci yöntemlerle bütçenizi dengeleyebilirsiniz.")
    if 3001 <= categories['ulaşım'] <= 4000:
        recommendations.append("Ulaşım harcamalarınız aşırı yüksek. Daha sürdürülebilir ve ekonomik seçeneklere odaklanabilirsiniz.")
    if 4001 <= categories['ulaşım'] <= 5000:
        recommendations.append("Ulaşım harcamalarınız kontrol dışına çıkmış görünüyor. Çevre dostu seçenekleri bir an önce benimseyin.")
    if categories['ulaşım'] > 5000:
        recommendations.append("Ulaşım harcamalarınızı toplu taşıma kullanarak azaltabilirsiniz.")
    
    if categories['diğer_giderler'] > 150:
        recommendations.append("Diğer giderlerinizi gözden geçirerek tasarruf sağlayabilirsiniz.")
    

    # Verileri 'environmental_advice.html' sayfasına gönder
    return render(request, 'account/environmental_advice.html', {
        'total_income': total_income,
        'total_expenses': total_expenses,
        'categories': categories,
        'recommendations': recommendations,
    })
