import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'onboarding_screen.dart'; // Import your new screen
import 'custom_transitions.dart'; // Import custom transitions
import 'firebase_config.dart'; // Import Firebase configuration
import 'services/chat_service.dart';
import 'services/theme_service.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await FirebaseConfig.initializeFirebase();
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (context) => ChatService()),
        ChangeNotifierProvider(create: (context) => ThemeService()),
      ],
      child: Consumer<ThemeService>(
        builder: (context, themeService, child) => MaterialApp(
        title: 'Y^2 App',
        themeMode: themeService.themeMode,
        theme: ThemeData(
          brightness: Brightness.light,
          colorScheme: ColorScheme.fromSeed(seedColor: Colors.blue, brightness: Brightness.light),
          scaffoldBackgroundColor: const Color(0xFFF7F7F7),
          pageTransitionsTheme: PageTransitionsTheme(
            builders: {
              TargetPlatform.android: FigmaInteractionPageTransitionsBuilder(),
              TargetPlatform.iOS: FigmaInteractionPageTransitionsBuilder(),
              TargetPlatform.macOS: FigmaInteractionPageTransitionsBuilder(),
              TargetPlatform.windows: FigmaInteractionPageTransitionsBuilder(),
              TargetPlatform.linux: FigmaInteractionPageTransitionsBuilder(),
            },
          ),
        ),
        darkTheme: ThemeData(
          brightness: Brightness.dark,
          colorScheme: ColorScheme.fromSeed(seedColor: Colors.blueGrey, brightness: Brightness.dark),
          scaffoldBackgroundColor: const Color(0xFF151515),
          pageTransitionsTheme: PageTransitionsTheme(
            builders: {
              TargetPlatform.android: FigmaInteractionPageTransitionsBuilder(),
              TargetPlatform.iOS: FigmaInteractionPageTransitionsBuilder(),
              TargetPlatform.macOS: FigmaInteractionPageTransitionsBuilder(),
              TargetPlatform.windows: FigmaInteractionPageTransitionsBuilder(),
              TargetPlatform.linux: FigmaInteractionPageTransitionsBuilder(),
            },
          ),
        ),
        // Set the OnboardingScreen as the home screen
        home: const OnboardingScreen(),
      ),
      ),
    );
  }
}
