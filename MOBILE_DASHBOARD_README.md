# School Management System - Mobile Dashboard

## ছবির মতো Mobile-First Responsive UI

আপনার School Management System এ এখন একটি সুন্দর mobile-first responsive dashboard যোগ করা হয়েছে যা ছবিতে দেখানো "Smart Pathshala" design এর মতো।

### Features:

1. **Mobile-First Design**: সম্পূর্ণ responsive এবং mobile devices এর জন্য optimized
2. **Beautiful UI**: Gradient colors, pastel themes এবং modern design
3. **School Info Card**: School এর নাম, প্রতিষ্ঠার সাল, ঠিকানা, ইমেইল এবং ফোন নম্বর
4. **Feature Grid**: 8টি main features (Student Attendance, Teachers Attendance, Accounts, Exam Results, Leave Management, Notification, Event, Resident)
5. **Quick Stats**: Students, Teachers, Classes এবং Attendance percentage
6. **Responsive**: সব screen sizes এ perfectly কাজ করে

### কিভাবে Access করবেন:

#### Option 1: Automatic Detection
- যেকোনো mobile device (Android/iPhone/iPad) থেকে dashboard open করলে automatically mobile view দেখাবে
- URL: `http://localhost:8000/dashboard`

#### Option 2: Manual Selection
- Desktop থেকেও mobile view দেখতে চাইলে:
- URL: `http://localhost:8000/dashboard?view=mobile`

### Customization:

আপনার school এর তথ্য update করতে `dashboard_mobile.html` file এ যান:

```html
<h2>FULKURI ISLAMIC ACADEMY</h2>
<p class="school-year">(Estd: 1982)</p>
```

এই অংশ পরিবর্তন করুন আপনার school এর নাম এবং প্রতিষ্ঠার সাল দিয়ে।

Contact information update করতে:

```html
<div class="contact-item">
    <i class="fas fa-map-marker-alt"></i>
    <span>Chapainwabganj-6300</span>
</div>
```

### Color Customization:

`mobile-dashboard.css` file এ colors customize করতে পারবেন:

```css
:root {
    --mint: #A8E6CF;
    --peach: #FFD3B6;
    --blue: #A0D8FF;
    --lavender: #E4B5FF;
    --pink: #FFB3BA;
    --yellow: #FFFFBA;
    --sky: #B4E7FF;
    --purple: #DDA0DD;
}
```

### Responsive Breakpoints:

- **Small Mobile**: 320px - 374px
- **Medium Mobile**: 375px - 480px
- **Large Mobile & Tablet**: 481px - 768px
- **Tablet & Small Desktop**: 769px - 1024px
- **Desktop**: 1025px+

### Browser Support:

- Chrome (Android & Desktop)
- Safari (iOS & macOS)
- Firefox
- Edge
- Opera

### Performance:

- Fast loading
- Smooth animations
- Touch-friendly
- Optimized for mobile networks

### Screenshots:

Mobile dashboard এ আপনি দেখতে পাবেন:

1. **Header**: Blue gradient background with school info
2. **Feature Cards**: 2-column grid with colorful icons
3. **Stats**: Quick overview of key metrics
4. **Navigation**: Direct links to all major features

### Support:

কোনো সমস্যা হলে বা আরো customization প্রয়োজন হলে যোগাযোগ করুন।

---

**Note**: এই mobile dashboard টি ছবিতে দেখানো "Smart Pathshala" design অনুসরণ করে তৈরি করা হয়েছে এবং সম্পূর্ণ responsive।
