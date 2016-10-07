'''
Created on Aug 6, 2016

@author: weizhenyuan
'''
from django.http import HttpResponse
from django.template.loader import get_template
from django.http import HttpResponseRedirect
from HealthModel.models import DoctorInfo, Product, PaymentType, BookingInfo
from HealthModel.models import ServiceType
from HealthModel.models import Membership
from HealthModel.models import Transaction
from HealthModel.models import ServiceRate
from datetime import date
from datetime import datetime
from datetime import timedelta
from django.views.decorators.csrf import csrf_exempt
from Health.Admin.common import createResponseDic

timeBJ = 8

class Payment :
    id = 0
    paymenttype = ''
    paymenttypename = ''
    vipname = ''
    vipno = ''
    doctorname = ''
    amount = 0
    servicename = ''
    productname = ''
    paymentdate = date.today()
    bookingId = ''

def goPrePayment(request):
    outDic = createResponseDic(request=request)
    outDic['hightlight'] = '5'
    doctorList = DoctorInfo.objects.all()
    outDic['doctorList'] = doctorList
    servicetypeList = ServiceType.objects.all()
    outDic['servicetypeList'] = servicetypeList
    productList = Product.objects.all()
    outDic['productList'] = productList
    #serviceRateList = ServiceRate.objects.all()
    #outDic['serviceRateList'] = serviceRateList
    
    try :
        bookingId = request.GET['id']
        bookingInfo = BookingInfo.objects.get(id = bookingId)
        outDic['bookingInfo'] = bookingInfo
        doctor = DoctorInfo.objects.get(id = bookingInfo.bookeddoctor)
        outDic['doctorname'] = doctor.doctorname
        service = ServiceType.objects.get(id = bookingInfo.bookeditem)
        outDic['servicename'] = service.servicename
    except :
        print '--------there is no booking pay '
    
    usedTemplate = get_template('admin/prepayment.html')
    html = usedTemplate.render(outDic)
    return HttpResponse(html)

@csrf_exempt
def doPrePayment(request):
    outDic = createResponseDic(request=request)
    outDic['hightlight'] = '5'
    
    try :
        paymenttype = '00'
        phonenumber = request.POST['phonenumber']
        doctor = request.POST['doctor']
        servicetype = request.POST['servicetype']
        #servicerate = request.POST['servicerate']
        #servicediscount = request.POST['servicediscount']
        servicediscount = 1
        membershipId = ''
        amount = 0
        serviceamount = 0
        productamount = 0
        
        #product amount 
        productIds = ''
        productList = []
        for key in request.POST.keys() :
            if key[0:7] == 'product' :
                productId = request.POST[key]
                product = Product.objects.get(id = productId)
                productamount = productamount + product.productprice
                productList.append(product)
                productIds = productIds + request.POST[key] + ','
        outDic['productList'] = productList
        outDic['productamount'] = productamount
        
        if doctor != '0' :
            doctorInfo = DoctorInfo.objects.get(id=doctor)
            outDic['doctorInfo'] = doctorInfo
        
        serviceamount = 0
        if servicetype != '0' :
            service = ServiceType.objects.get(id=servicetype)
            serviceamount = service.servicerate
            outDic['service'] = service
            
        #Membership check
        if phonenumber != '' :
            try :
                membership = Membership.objects.get(phonenumber=phonenumber)
            except :
                try :
                    membership = Membership.objects.get(vipno=phonenumber)
                except :
                    membership = None
            if membership != None :
                servicediscount = membership.discountrate
                membershipId = membership.id
                phonenumber = membership.phonenumber
                now = (timedelta(hours=timeBJ) + datetime.now()).strftime('%H')
                if now < '13' :
                    servicediscount = membership.discountrate2
                    
                outDic['membership'] = membership
            
        
        amount = serviceamount * float(servicediscount) + productamount
        
        outDic['amount'] = amount
        outDic['paymenttype'] = paymenttype
        outDic['phonenumber'] = phonenumber
        outDic['doctor'] = doctor
        outDic['servicetype'] = servicetype
        outDic['serviceamount'] = serviceamount
        outDic['amount'] = amount
        outDic['servicediscount'] = servicediscount
        today = datetime.now() + timedelta(hours=timeBJ)
        
        #save to transaction
        bookingId = ''
        try : 
            bookingId = request.POST['bookingId']
            if bookingId == '' :
                raise Exception('for no booking, than can mutil-payment')
            transaction = Transaction.objects.get(bookingId = bookingId, successFlag = '0')
            outDic['transactionId'] = transaction.id
        except :
            transaction = Transaction()
            transaction.membershipId = membershipId
            transaction.bookingId = bookingId
            transaction.doctorId = doctor
            transaction.servicetypeId = servicetype
            transaction.amount = amount
            transaction.productamount = productamount
            transaction.serviceamount = serviceamount
            transaction.productIds = productIds
            transaction.discount = float(servicediscount)
            transaction.paymentType = paymenttype
            transaction.successFlag = '0'
            transaction.transactionDate = today
            transaction.save()
            outDic['transactionId'] = transaction.id
        
    except :
        print '--------there is no membership : phonenumber = ' + phonenumber + '------------'
        outDic['isMessage'] = 'OK'
        doctorList = DoctorInfo.objects.all()
        servicetypeList = ServiceType.objects.all()
        outDic['doctorList'] = doctorList
        outDic['servicetypeList'] = servicetypeList
        usedTemplate = get_template('admin/prepayment.html')
        html = usedTemplate.render(outDic)
        return HttpResponse(html)
    finally:
        usedTemplate = get_template('admin/prepaymentresult.html')
        html = usedTemplate.render(outDic)
        return HttpResponse(html)

def goPaymentTypeSelect(request):
    outDic = createResponseDic(request=request)
    outDic['hightlight'] = '5'
    isMembership = True
    try :
        transactionIds = ''
        for key in request.GET.keys() :
            if key[0:13] == 'transactionId' :
                transactionId = request.GET[key]
                transactionIds = transactionIds + transactionId + ','
                transaction = Transaction.objects.get(id = transactionId)
                if transaction.membershipId == '' :
                    isMembership = False
        outDic['transactionIds'] = transactionIds
    except :
        outDic['messages'] = 'ERROR'
    
    paymentTypeList = PaymentType.objects.all()
    if not isMembership :
        paymentTypeList = paymentTypeList.exclude(paymenttype = '02')
    outDic['paymentTypeList'] = paymentTypeList
    
    usedTemplate = get_template('admin/paymenttypeselect.html')
    html = usedTemplate.render(outDic)
    return HttpResponse(html)

@csrf_exempt
def doPaymentTypeSelect(request):
    outDic = createResponseDic(request=request)
    outDic['hightlight'] = '5'
    
    try :
        transactionIds = request.POST['transactionIds'].split(',')
        paymentList = []
        serviceAmount = 0
        prodctAmount = 0
        amount = 0
        paymenttypename = ''
        for transactionId in transactionIds :
            if transactionId != '' :
                transaction = Transaction.objects.get(id = transactionId)
                serviceAmount = serviceAmount + transaction.serviceamount * transaction.discount
                prodctAmount = prodctAmount + transaction.productamount
                amount = amount + transaction.amount
                payment = createPayment(transaction = transaction)
                paymentList.append(payment)
        outDic['paymentList'] = paymentList
        outDic['serviceAmount'] = serviceAmount
        outDic['prodctAmount'] = prodctAmount
        outDic['amount'] = amount
        outDic['transactionIds'] = request.POST['transactionIds']
        try :
            paymenttype = request.POST['paymenttype']
            outDic['paymenttype'] = paymenttype
            paymenttypename = PaymentType.objects.get(paymenttype = paymenttype).paymenttypename
            outDic['paymenttypename'] = paymenttypename
            usedTemplate = get_template('admin/prepaymentlist.html')
            
        except :
            outDic['messages'] = 'NOPAYMENTTYPE'
            paymentTypeList = PaymentType.objects.all()
            outDic['paymentTypeList'] = paymentTypeList
            usedTemplate = get_template('admin/paymenttypeselect.html')
        
    except :
        outDic['messages'] = 'ERROR'
        
    
    html = usedTemplate.render(outDic)
    return HttpResponse(html)

@csrf_exempt
def doPayment(request):
    outDic = createResponseDic(request=request)
    outDic['hightlight'] = '5'
    
    try :
        transactionIds = request.POST['transactionIds'].split(',')
        paymentType = request.POST['paymenttype']
        paymentList = []
        serviceAmount = 0
        prodctAmount = 0
        amount = 0
        membershipId = ''
        isSave = True
        #Calculate the total amount
        for transactionId in transactionIds :
            if transactionId != '' :
                transaction = Transaction.objects.get(id = transactionId)
                membershipId = transaction.membershipId
 
                successFlag = transaction.successFlag
                if successFlag != 1 :
                    serviceAmount = serviceAmount + transaction.serviceamount * transaction.discount
                    prodctAmount = prodctAmount + transaction.productamount
                    amount = amount + transaction.amount
        
        #check the member card amount        
        if paymentType == '02' :
            membership = Membership.objects.get(id = membershipId)
            lastamount = membership.amount
            membership.lastamount = lastamount
            membershipAmount = lastamount - amount
            if membershipAmount >= 0 :
                membership.amount = membershipAmount
                membership.save()
            else :
                isSave = False
                outDic['messages'] = 'ERROR'
        
        #do payment        
        if isSave :
            for transactionId in transactionIds :
                if transactionId != '' :
                    transaction = Transaction.objects.get(id = transactionId)
                    successFlag = transaction.successFlag
                    if successFlag != 1 :
                        transaction.paymentType = paymentType
                        transaction.successFlag = '1'
                        transaction.save()  
                    
                    payment = createPayment(transaction = transaction)
                    paymentList.append(payment)
                    
                    #complete the booking
                    bookingId = transaction.bookingId
                    if bookingId != '' :
                        try :
                            bookingInfo = BookingInfo.objects.get(id = bookingId)
                            bookingInfo.status = '9'
                            bookingInfo.save()
                        except :
                            print '--------the booking info is not exist. Id = ' + bookingId
                            
        outDic['paymentList'] = paymentList
        outDic['serviceAmount'] = serviceAmount
        outDic['prodctAmount'] = prodctAmount
        outDic['amount'] = amount
    except :
        outDic['messages'] = 'FAILT'
    
    usedTemplate = get_template('admin/prepaymentresultlist.html')
    html = usedTemplate.render(outDic)
    return HttpResponse(html)

def createPayment(transaction):
    payment = Payment()
    payment.id = transaction.id
    payment.paymenttype = transaction.paymentType
    payment.amount = transaction.amount
    payment.paymentdate = transaction.transactionDate
    payment.bookingId = transaction.bookingId
    payment.successFlag = transaction.successFlag
    
    try :
        paymentType = PaymentType.objects.get(paymenttype = transaction.paymentType)
        payment.paymenttypename = paymentType.paymenttypename
    except :
        payment.paymenttypename = ''
        
    try :    
        membership = Membership.objects.get(id=transaction.membershipId)
        payment.vipname = membership.vipname
        payment.vipno = membership.vipno
    except :
        payment.vipname = ''
        payment.vipno = ''
        
    try :    
        doctor = DoctorInfo.objects.get(id=transaction.doctorId)
        payment.doctorname = doctor.doctorname
    except :
        payment.doctorname = ''
        
    try :
        service = ServiceType.objects.get(id=transaction.servicetypeId)
        payment.servicename = service.servicename
    except :
        payment.servicename = ''
    
    try :
        productNames = ''
        for productId in transaction.productIds.split(',') :
            if productId != '' :
                product = Product.objects.get(id = productId)
                productNames = productNames + product.productname + ' & '
        productNames = productNames[0:len(productNames) - 3]
        if transaction.successFlag == '9' :
            productNames = 'Recharge'
        payment.productname = productNames
    except :
        payment.servicename = ''
        
    return payment

def goUnpayedList(request):
    outDic = createResponseDic(request=request)
    outDic['hightlight'] = '5'
    
    transactionList = Transaction.objects.filter(successFlag = '0')
    paymentList = []
    for transaction in transactionList :
        payment = createPayment(transaction = transaction)
        paymentList.append(payment)
    outDic['paymentList'] = paymentList
    
    usedTemplate = get_template('admin/unpayedlist.html')
    html = usedTemplate.render(outDic)
    return HttpResponse(html)

def doDeleteUnpayed(request):
    outDic = createResponseDic(request=request)
    outDic['hightlight'] = '5'
    
    transactionId = request.GET['transactionId']
    try :
        transaction = Transaction.objects.get(id = transactionId)
        transaction.delete()
    except :
        print '----------------the transaction that you want to delete is not exist. Tansaction ID : ' + transactionId
    
    transactionList = Transaction.objects.filter(successFlag = '0')
    paymentList = []
    for transaction in transactionList :
        payment = createPayment(transaction = transaction)
        paymentList.append(payment)
    outDic['paymentList'] = paymentList
    
    usedTemplate = get_template('admin/unpayedlist.html')
    html = usedTemplate.render(outDic)
    return HttpResponse(html)

def goPaymentList(request):
    outDic = createResponseDic(request=request)
    outDic['hightlight'] = '6'
    
    #query form show
    dayList = []
    tempday = datetime.now()
    for i in range(0, 8) :
        dayList.append((tempday + timedelta(days=-i)).strftime('%Y-%m-%d'))
    outDic['dayList'] = dayList
    doctrList = DoctorInfo.objects.all()
    outDic['doctrList'] = doctrList
    #query form show
        
    today = str(date.today())
    paymentList = getPaymentList(querydate=today)
    outDic['paymentList'] = paymentList
    usedTemplate = get_template('admin/paymentlist.html')
    html = usedTemplate.render(outDic)
    return HttpResponse(html)

def searchPaymentList(request):
    outDic = createResponseDic(request=request)
    outDic['hightlight'] = '6'
    
    #query form show
    dayList = []
    tempday = datetime.now()
    for i in range(0, 8) :
        dayList.append((tempday + timedelta(days=-i)).strftime('%Y-%m-%d'))
    outDic['dayList'] = dayList
    doctrList = DoctorInfo.objects.all()
    outDic['doctrList'] = doctrList
    #query form show
    
    querydate = request.GET['querydate']
    doctorId = request.GET['doctorid']
    paymentList = getPaymentList(querydate=querydate, doctorId=doctorId)
    outDic['paymentList'] = paymentList
    usedTemplate = get_template('admin/paymentlist.html')
    html = usedTemplate.render(outDic)
    return HttpResponse(html)

def getPaymentList(querydate='', doctorId='', queryyear='', querymonth=''):
    
    transactionList = Transaction.objects.all()
    
    if querydate != '' :
        transactionList = Transaction.objects.filter(transactionDate=querydate)
    
    if queryyear != '' :
        transactionList = Transaction.objects.filter(transactionDate__year=queryyear)
    
    if querymonth != '' :
        transactionList = Transaction.objects.filter(transactionDate__month=querymonth)
    
    if doctorId != '' :
        transactionList = transactionList.filter(doctorId=doctorId)
        
    transactionList = transactionList.exclude(successFlag='0')
    transactionList = transactionList.exclude(successFlag='8')
    
    paymentList = []
    totalamount = 0
    for transaction in transactionList :
        payment = createPayment(transaction = transaction)
        paymentList.append(payment)
        totalamount = totalamount + transaction.amount
    
    payment = Payment()
    payment.servicename = 'Total'
    payment.amount = totalamount
    
    summarydate = ''
    if querydate != '' :
        summarydate = datetime.strptime(querydate, '%Y-%m-%d').date
    if queryyear != '' :
        summarydate = queryyear
    if querymonth != '' :
        summarydate = summarydate + '-' +querymonth
        
    payment.paymentdate = summarydate
    paymentList.append(payment)
    return paymentList

def goPaymentSummaryList(request):
    outDic = createResponseDic(request=request)
    outDic['hightlight'] = '6'
    
    #query form show
    yearList = []
    year = datetime.strftime(date.today(), '%Y')
    for i in range(0, 5) :
        yearList.append(int(year) - i)
    outDic['yearList'] = yearList
    doctrList = DoctorInfo.objects.all()
    outDic['doctrList'] = doctrList
    #query form show
        
    #today = str(date.today())
    paymentList = getPaymentList(queryyear=year)
    outDic['paymentList'] = paymentList
    usedTemplate = get_template('admin/paymentsummarylist.html')
    html = usedTemplate.render(outDic)
    return HttpResponse(html)

def searchPaymentSummaryList(request):
    outDic = createResponseDic(request=request)
    outDic['hightlight'] = '6'
    
    #query form show
    yearList = []
    year = datetime.strftime(date.today(), '%Y')
    for i in range(0, 5) :
        yearList.append(int(year) - i)
    outDic['yearList'] = yearList
    doctrList = DoctorInfo.objects.all()
    outDic['doctrList'] = doctrList
    #query form show
        
    queryyear = request.GET['queryyear']
    querymonth = request.GET['querymonth']
    doctorId = request.GET['doctorid']
    paymentList = getPaymentList(queryyear=queryyear, querymonth=querymonth, doctorId=doctorId)
    outDic['paymentList'] = paymentList
    usedTemplate = get_template('admin/paymentsummarylist.html')
    html = usedTemplate.render(outDic)
    return HttpResponse(html)

def goAccounting(request):
    outDic = createResponseDic(request=request)
    outDic['hightlight'] = '6'
    
    today = datetime.now() + timedelta(hours=timeBJ)
    paymentList = []
    paymentTypeList = PaymentType.objects.all()
    for tmpPaymentType in paymentTypeList:
        payment = Payment()
        payment.paymenttypename = tmpPaymentType.paymenttypename
        paymenttype = tmpPaymentType.paymenttype
        transactionList = Transaction.objects.filter(transactionDate = today)
        transactionList = transactionList.filter(paymentType = paymenttype)
        transactionList = transactionList.exclude(successFlag = '0')
        amount = 0
        for transaction in transactionList :
            amount = amount + transaction.amount
        payment.amount = amount
        paymentList.append(payment)
        
    outDic['paymentList'] = paymentList   
    usedTemplate = get_template('admin/accounting.html')
    html = usedTemplate.render(outDic)
    return HttpResponse(html)

def deletePayment(request):
    id = request.GET['id']
    try :
        transaction = Transaction.objects.get(id = id)
        transaction.delete()
    except :
        print '-------------there is no transaction id = ' + id
        
    finally: 
        return HttpResponseRedirect('../gopaymentlist/')
    
def cancelPayment(request):
    id = request.GET['id']
    try :
        transaction = Transaction.objects.get(id = id)
        successFlag = transaction.successFlag
        if successFlag == '1' :
            transaction.successFlag = '8'
            transaction.save()
            
            membershipId = transaction.membershipId
            if membershipId != '' :
                amount = transaction.amount
                membership = Membership.objects.get(id = membershipId)
                membership.amount = membership.amount + amount
                membership.save()
            
            bookingId = transaction.bookingId
            if bookingId != '' :
                bookingInfo = BookingInfo.objects.get(id = bookingId)
                bookingInfo.status = '1'
                bookingInfo.save()
         
    except :
        print '-------------there is no transaction id = ' + id
        
    finally: 
        return HttpResponseRedirect('../gopaymentlist/')

