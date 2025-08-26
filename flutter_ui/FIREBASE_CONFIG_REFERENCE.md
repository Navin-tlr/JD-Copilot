# 🔥 Firebase Configuration Reference Card

## 📋 Configuration Values You Need

Copy these values from your Firebase project and paste them in `lib/firebase_options_real.dart`:

### 🌐 Web Configuration
```dart
static const FirebaseOptions web = FirebaseOptions(
  apiKey: 'PASTE_YOUR_WEB_API_KEY_HERE',
  appId: 'PASTE_YOUR_WEB_APP_ID_HERE',
  messagingSenderId: 'PASTE_YOUR_SENDER_ID_HERE',
  projectId: 'PASTE_YOUR_PROJECT_ID_HERE',
  authDomain: 'PASTE_YOUR_PROJECT_ID_HERE.firebaseapp.com',
  storageBucket: 'PASTE_YOUR_PROJECT_ID_HERE.appspot.com',
  measurementId: 'PASTE_YOUR_MEASUREMENT_ID_HERE', // Optional
);
```

### 📱 Android Configuration
```dart
static const FirebaseOptions android = FirebaseOptions(
  apiKey: 'PASTE_YOUR_ANDROID_API_KEY_HERE',
  appId: 'PASTE_YOUR_ANDROID_APP_ID_HERE',
  messagingSenderId: 'PASTE_YOUR_SENDER_ID_HERE',
  projectId: 'PASTE_YOUR_PROJECT_ID_HERE',
  storageBucket: 'PASTE_YOUR_PROJECT_ID_HERE.appspot.com',
);
```

### 🍎 iOS Configuration
```dart
static const FirebaseOptions ios = FirebaseOptions(
  apiKey: 'PASTE_YOUR_IOS_API_KEY_HERE',
  appId: 'PASTE_YOUR_IOS_APP_ID_HERE',
  messagingSenderId: 'PASTE_YOUR_SENDER_ID_HERE',
  projectId: 'PASTE_YOUR_PROJECT_ID_HERE',
  storageBucket: 'PASTE_YOUR_PROJECT_ID_HERE.appspot.com',
  iosBundleId: 'com.example.flutterUi',
);
```

## 🔍 Where to Find These Values

1. **Firebase Console** → Your Project
2. **Project Settings** (gear icon)
3. **Your Apps** section
4. **Select your Flutter app**
5. **Copy the configuration object**

## ⚠️ Important Notes

- **Project ID**: Same for all platforms
- **API Keys**: Different for each platform (web/Android/iOS)
- **App IDs**: Different for each platform
- **Sender ID**: Same for all platforms
- **Bundle ID**: Should match your app's bundle identifier

## 🚀 Quick Setup Checklist

- [ ] Firebase project created
- [ ] Authentication enabled
- [ ] Database created
- [ ] Flutter app added to Firebase
- [ ] Configuration values copied
- [ ] `firebase_options_real.dart` updated
- [ ] `firebase_config.dart` updated to use real config
- [ ] App restarted
- [ ] Firebase connects successfully

## 📞 Need Help?

If you can't find any of these values:
1. Make sure you've added your Flutter app to Firebase
2. Check that you're in the right project
3. Verify the app registration was successful

---

**Copy these values exactly as they appear in Firebase Console!** 🎯
