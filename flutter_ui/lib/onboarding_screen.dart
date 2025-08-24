import 'package:flutter/material.dart';
import 'create_account_screen.dart'; // Import the Create Account screen

class OnboardingScreen extends StatefulWidget {
  const OnboardingScreen({super.key});

  @override
  State<OnboardingScreen> createState() => _OnboardingScreenState();
}

class _OnboardingScreenState extends State<OnboardingScreen>
    with SingleTickerProviderStateMixin {
  late AnimationController _animationController;
  late Animation<double> _scaleAnimation;
  bool _isHovered = false;

  @override
  void initState() {
    super.initState();
    _animationController = AnimationController(
      duration: const Duration(milliseconds: 150),
      vsync: this,
    );
    _scaleAnimation = Tween<double>(
      begin: 1.0,
      end: 0.95,
    ).animate(CurvedAnimation(
      parent: _animationController,
      curve: Curves.easeInOut,
    ));
  }

  @override
  void dispose() {
    _animationController.dispose();
    super.dispose();
  }

  void _onButtonPressed() {
    _animationController.forward().then((_) {
      _animationController.reverse();
    });
    
    // Navigate to Create Account screen
    Navigator.push(
      context,
      MaterialPageRoute(builder: (context) => const CreateAccountScreen()),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      body: Center(
        child: Container(
          width: 393, // Exact Figma frame width
          height: 852, // Exact Figma frame height
          child: Stack(
            children: [
              // Layer 1: The background "Y" image, positioned exactly like Figma
              Positioned(
                left: 42.77, // Exact Figma positioning
                top: 208.68, // Exact Figma positioning
                child: Opacity(
                  opacity: 0.28,
                  child: Image.asset(
                    'assets/images/y_logo.png',
                    width: 279.834, // Exact Figma width
                    height: 435.414, // Exact Figma height
                    fit: BoxFit.contain,
                  ),
                ),
              ),

              // Layer 2: "WELCOME TO Y^2" text, positioned exactly like Figma
              Positioned(
                left: 57.491, // Calculated: (393 - 278.018) / 2 = 57.491
                top: 71.11, // Exact Figma positioning
                child: Text(
                  'WELCOME TO Y^2',
                  textAlign: TextAlign.center,
                  style: TextStyle(
                    fontFamily: 'That That New Pixel Test',
                    fontSize: 38,
                    color: Color(0xFF2A2727),
                    fontWeight: FontWeight.w400,
                  ),
                ),
              ),

              // Layer 3: The "SIGN UP / LOG IN" button with interactions
              Positioned(
                left: 110, // Exact Figma positioning
                top: 749, // Exact Figma positioning
                child: MouseRegion(
                  onEnter: (_) => setState(() => _isHovered = true),
                  onExit: (_) => setState(() => _isHovered = false),
                  child: AnimatedBuilder(
                    animation: _scaleAnimation,
                    builder: (context, child) {
                      return Transform.scale(
                        scale: _scaleAnimation.value,
                        child: OutlinedButton(
                          onPressed: _onButtonPressed,
                          style: OutlinedButton.styleFrom(
                            fixedSize: const Size(172, 46), // Exact Figma dimensions
                            side: BorderSide(
                              color: _isHovered 
                                  ? Colors.black.withOpacity(0.6) // Darker on hover
                                  : Colors.black.withOpacity(0.3),
                              width: _isHovered ? 2 : 1, // Thicker on hover
                            ),
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(12),
                            ),
                            backgroundColor: _isHovered 
                                ? Colors.black.withOpacity(0.05) // Subtle background on hover
                                : Colors.transparent,
                          ),
                          child: Text(
                            'SIGN UP / LOG IN',
                            style: TextStyle(
                              fontFamily: 'PP NeueBit',
                              fontSize: 18,
                              fontWeight: FontWeight.bold,
                              color: _isHovered 
                                  ? Colors.black.withOpacity(0.8) // Darker text on hover
                                  : const Color(0xFF646262).withOpacity(0.7),
                            ),
                          ),
                        ),
                      );
                    },
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
