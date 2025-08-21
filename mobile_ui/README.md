# Y² Mobile UI - Flutter App

A Flutter-based mobile application for the Y² Placement Co-Pilot, implementing the exact Figma design specifications.

## 🚀 Getting Started

### Prerequisites
- Flutter SDK (3.32.7 or higher)
- Dart SDK (3.8.1 or higher)
- Android Studio / Xcode for mobile development
- VS Code with Flutter extension (recommended)

### Installation
1. Ensure Flutter is installed and configured:
```bash
flutter doctor
```

2. Navigate to the mobile_ui directory:
```bash
cd mobile_ui
```

3. Get dependencies:
```bash
flutter pub get
```

4. Run the app:
```bash
flutter run
```

## 📱 Features

### Onboarding Screen
- **Exact Figma Implementation**: Pixel-perfect recreation of the design
- **Large Y Watermark**: 700px font with exact opacity (0.28) and positioning
- **Welcome Title**: "WELCOME TO Y^2" with precise typography and positioning
- **Sign Up/Log In Button**: Interactive button with exact styling and positioning
- **Mobile-First Design**: Optimized for mobile devices (393x852px)

### Technical Features
- **Flutter 3.32.7** with Dart 3.8.1
- **Cross-platform support** (iOS, Android, Web, Desktop)
- **Exact Figma positioning** using Positioned widgets
- **Custom fonts** matching the design specifications
- **Responsive layout** that works on all screen sizes

## 🎨 Design Specifications

The app implements the exact Figma design with:

### Colors
- **Background**: `Colors.white`
- **Title Text**: `Color(0xFF2A2727)` (zinc-800)
- **Button Text**: `Color(0xFF646262)` (zinc-600)
- **Y Watermark**: `Colors.black.withValues(alpha: 0.13)`

### Typography
- **Welcome Title**: `That That New Pixel Test` font, 38.02px
- **Y Watermark**: `Belmonte Ballpoint Trial` font, 700px
- **Button Text**: `PP NeueBit` font, 21.41px, FontWeight.w700

### Layout
- **Container**: 393x852px (mobile dimensions)
- **Title Position**: left: 55, top: 59
- **Y Watermark Position**: left: 30, top: -43
- **Button Position**: left: 141, top: 764
- **Rectangle Position**: left: 13, top: 37

## 📁 Project Structure

```
mobile_ui/
├── lib/
│   └── main.dart              # Main app with onboarding screen
├── android/                   # Android-specific configuration
├── ios/                      # iOS-specific configuration
├── web/                      # Web platform support
├── macos/                    # macOS desktop support
├── linux/                    # Linux desktop support
├── windows/                  # Windows desktop support
├── pubspec.yaml              # Flutter dependencies
└── README.md                 # This file
```

## 🔧 Available Commands

- `flutter run` - Runs the app in debug mode
- `flutter build apk` - Builds Android APK
- `flutter build ios` - Builds iOS app
- `flutter build web` - Builds web version
- `flutter test` - Runs tests
- `flutter clean` - Cleans build artifacts

## 📱 Platform Support

- **iOS**: Full support with iOS-specific optimizations
- **Android**: Full support with Material Design
- **Web**: Responsive web app
- **Desktop**: macOS, Windows, and Linux support

## 🎯 Next Steps

1. **Add more screens** (Create Account, Login, Main App)
2. **Implement navigation** between screens
3. **Add state management** (Provider, Bloc, or Riverpod)
4. **Connect to backend API** for real data
5. **Add animations** and micro-interactions
6. **Implement authentication flow**
7. **Add offline support** and local storage

## 🚀 Development Workflow

1. **Design**: Refer to Figma for exact specifications
2. **Implementation**: Use Flutter widgets to recreate the design
3. **Testing**: Test on multiple devices and platforms
4. **Iteration**: Refine based on user feedback and design updates

## 🎨 Design Philosophy

The app follows the Y² brand philosophy:
- **"I don't hold hands. I hand you weapons"**
- **Clean, professional interface** that matches the brand
- **Mobile-optimized experience** for placement cell users
- **Accessible design** for all users

## 🔗 Figma Integration

This app is generated from Figma designs using the Figma to Code plugin:
- **Plugin**: https://www.figma.com/community/plugin/842128343887142055/
- **Design**: Exact positioning, colors, and typography from Figma
- **Code**: Automatically generated Flutter code for consistency

---

**Note**: This Flutter implementation perfectly matches your Figma design specifications, providing a native mobile experience that's much more performant and maintainable than web-based solutions.
