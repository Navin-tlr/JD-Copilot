import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'specialization_screen.dart';

class CreateAccountScreen extends StatefulWidget {
  const CreateAccountScreen({super.key});

  @override
  State<CreateAccountScreen> createState() => _CreateAccountScreenState();
}

class _CreateAccountScreenState extends State<CreateAccountScreen> 
    with SingleTickerProviderStateMixin {
  final TextEditingController _emailController = TextEditingController();
  final TextEditingController _passwordController = TextEditingController();
  bool _isLoading = false;
  late AnimationController _buttonAnimationController;
  late Animation<double> _buttonScaleAnimation;

  @override
  void initState() {
    super.initState();
    _buttonAnimationController = AnimationController(
      duration: const Duration(milliseconds: 150),
      vsync: this,
    );
    _buttonScaleAnimation = Tween<double>(
      begin: 1.0,
      end: 0.96,
    ).animate(CurvedAnimation(
      parent: _buttonAnimationController,
      curve: Curves.easeInOut,
    ));
  }

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    _buttonAnimationController.dispose();
    super.dispose();
  }

  void _onCreateAccountPressed() async {
    if (_isLoading) return;

    // Validate inputs
    if (_emailController.text.isEmpty || _passwordController.text.isEmpty) {
      _showErrorSnackBar('Please fill in all fields');
      return;
    }

    if (!_isValidEmail(_emailController.text)) {
      _showErrorSnackBar('Please enter a valid email address');
      return;
    }

    // Enhanced Apple-style haptic feedback and animation
    HapticFeedback.mediumImpact();
    await _playEnhancedButtonAnimation();

    setState(() => _isLoading = true);
    
    try {
      // TODO: Implement actual account creation logic here
      // For now, simulate API call
      await _simulateAccountCreation();
      
      // Navigate to specialization screen with enhanced transition
      if (mounted) {
        Navigator.of(context).pushReplacement(
          PageRouteBuilder(
            pageBuilder: (context, animation, secondaryAnimation) => 
                const SpecializationScreen(),
            transitionsBuilder: (context, animation, secondaryAnimation, child) {
              return FadeTransition(
                opacity: CurvedAnimation(
                  parent: animation,
                  curve: Curves.easeInOut,
                ),
                child: SlideTransition(
                  position: Tween<Offset>(
                    begin: const Offset(0, 0.2),
                    end: Offset.zero,
                  ).animate(CurvedAnimation(
                    parent: animation,
                    curve: Curves.easeOutCubic,
                  )),
                  child: ScaleTransition(
                    scale: Tween<double>(
                      begin: 0.95,
                      end: 1.0,
                    ).animate(CurvedAnimation(
                      parent: animation,
                      curve: Curves.easeOutBack,
                    )),
                    child: child,
                  ),
                ),
              );
            },
            transitionDuration: const Duration(milliseconds: 800),
          ),
        );
      }
    } catch (e) {
      _showErrorSnackBar('Something went wrong. Please try again.');
    } finally {
      if (mounted) {
        setState(() => _isLoading = false);
      }
    }
  }

  Future<void> _playEnhancedButtonAnimation() async {
    // Multi-stage button animation
    _buttonAnimationController.forward();
    await Future.delayed(const Duration(milliseconds: 150));
    _buttonAnimationController.reverse();
    
    // Add success haptic feedback
    HapticFeedback.heavyImpact();
    
    // Small bounce effect
    await Future.delayed(const Duration(milliseconds: 100));
    _buttonAnimationController.forward();
    await Future.delayed(const Duration(milliseconds: 100));
    _buttonAnimationController.reverse();
  }

  bool _isValidEmail(String email) {
    return RegExp(r'^[\w-\.]+@([\w-]+\.)+[\w-]{2,4}$').hasMatch(email);
  }

  Future<void> _simulateAccountCreation() async {
    // Simulate network call
    await Future.delayed(const Duration(milliseconds: 800));
  }

  void _showErrorSnackBar(String message) {
    HapticFeedback.heavyImpact();
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(
          message,
          style: TextStyle(
            fontFamily: 'PP Mondwest',
            fontSize: 14,
            fontWeight: FontWeight.w500,
          ),
        ),
        backgroundColor: Colors.red.shade600,
        behavior: SnackBarBehavior.floating,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12),
        ),
        margin: EdgeInsets.all(16),
        duration: Duration(seconds: 3),
      ),
    );
  }

  void _onLogInPressed() {
    Navigator.pop(context);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      body: Center(
        child: Container(
          width: 393, // Exact Figma frame width
          height: 852, // Exact Figma frame height
          // Background image with proper cover and centering
          decoration: BoxDecoration(
            image: DecorationImage(
              image: AssetImage('assets/images/background_landscape.jpg'),
              fit: BoxFit.cover,
              alignment: Alignment.center,
            ),
          ),
          // Main content container with exact Figma layout
          child: Stack(
            children: [
              // White card container - positioned exactly like Figma
              Positioned(
                left: 29, // Exact Figma positioning
                top: 356, // Exact Figma positioning
                child: Container(
                  width: 335, // Exact Figma width
                  height: 470, // Exact Figma height
                  decoration: BoxDecoration(
                    color: Colors.white, // #FFF
                    borderRadius: BorderRadius.circular(16), // Exact Figma border-radius: 16px
                    boxShadow: [
                      BoxShadow(
                        color: Colors.black.withOpacity(0.25), // Exact Figma: rgba(0, 0, 0, 0.25)
                        blurRadius: 4, // Exact Figma: 4px
                        offset: Offset(0, 4), // Exact Figma: 0 4px
                      ),
                    ],
                  ),
                  child: Stack(
                    children: [
                      // "Create Account" title - perfectly centered like Figma
                      Positioned(
                        left: 42.5, // Perfectly centered: (335 - 250) / 2 = 42.5px
                        top: 92, // Exact Figma positioning
                        child: Container(
                          width: 250, // Title width for proper centering
                          child: Text(
                            'Create\naccount', // Clean two-line format matching Figma
                            textAlign: TextAlign.center,
                            style: TextStyle(
                              fontFamily: 'PP Mondwest', // Exact Figma font
                              fontSize: 55, // Exact Figma size
                              fontWeight: FontWeight.w400, // Exact Figma weight
                              color: Color(0xFF000000), // Exact Figma color: black
                              height: 0.727, // Exact Figma line-height: 40px (72.727%)
                              letterSpacing: 0,
                            ),
                          ),
                        ),
                      ),

                      // Email input field - exact Figma positioning and styling
                      Positioned(
                        left: 43, // Exact Figma positioning
                        top: 221, // Exact Figma positioning
                        child: Container(
                          width: 250, // Exact Figma width
                          height: 54, // Exact Figma height
                          decoration: BoxDecoration(
                            color: Colors.white,
                            borderRadius: BorderRadius.circular(15.5), // Exact Figma: rx="15.5"
                            border: Border.all(
                              color: Color(0xFF646262).withOpacity(0.6), // Exact Figma: stroke="#646262" opacity="0.6"
                              width: 1, // Exact Figma: stroke-width="1px"
                            ),
                          ),
                          child: TextField(
                            controller: _emailController,
                            style: TextStyle(
                              fontFamily: 'PP Mondwest',
                              fontSize: 16,
                              fontWeight: FontWeight.w400,
                              color: Color(0xFF2A2727),
                            ),
                            decoration: InputDecoration(
                              hintText: 'Email Address',
                              hintStyle: TextStyle(
                                fontFamily: 'PP Mondwest',
                                fontSize: 14,
                                fontWeight: FontWeight.w400,
                                color: Color(0xFF646262).withOpacity(0.6),
                              ),
                              border: InputBorder.none,
                              contentPadding: EdgeInsets.symmetric(
                                horizontal: 20,
                                vertical: 18,
                              ),
                            ),
                          ),
                        ),
                      ),

                      // Password input field - exact Figma positioning and styling
                      Positioned(
                        left: 43, // Exact Figma positioning
                        top: 291, // Exact Figma positioning
                        child: Container(
                          width: 250, // Exact Figma width
                          height: 54, // Exact Figma height
                          decoration: BoxDecoration(
                            color: Colors.white,
                            borderRadius: BorderRadius.circular(15.5), // Exact Figma: rx="15.5"
                            border: Border.all(
                              color: Color(0xFF646262).withOpacity(0.6), // Exact Figma: stroke="#646262" opacity="0.6"
                              width: 1, // Exact Figma: stroke-width="1px"
                            ),
                          ),
                          child: TextField(
                            controller: _passwordController,
                            obscureText: true,
                            style: TextStyle(
                              fontFamily: 'PP Mondwest',
                              fontSize: 16,
                              fontWeight: FontWeight.w400,
                              color: Color(0xFF2A2727),
                            ),
                            decoration: InputDecoration(
                              hintText: 'Password',
                              hintStyle: TextStyle(
                                fontFamily: 'PP Mondwest',
                                fontSize: 14,
                                fontWeight: FontWeight.w400,
                                color: Color(0xFF646262).withOpacity(0.6),
                              ),
                              border: InputBorder.none,
                              contentPadding: EdgeInsets.symmetric(
                                horizontal: 20,
                                vertical: 18,
                              ),
                            ),
                          ),
                        ),
                      ),

                      // Create Account button - Apple-style with loading animation
                      Positioned(
                        left: 43, // Exact Figma positioning
                        top: 361, // Exact Figma positioning
                        child: AnimatedBuilder(
                          animation: _buttonScaleAnimation,
                          builder: (context, child) {
                            return Transform.scale(
                              scale: _buttonScaleAnimation.value,
                              child: AnimatedContainer(
                                duration: Duration(milliseconds: 200),
                                width: 250, // Exact Figma width
                                height: 54, // Exact Figma height
                                decoration: BoxDecoration(
                                  color: _isLoading
                                      ? Color(0xFF4E9816).withOpacity(0.6)
                                      : Color(0xFF4E9816).withOpacity(0.7), // Exact Figma: fill="#4E9816" opacity="0.7"
                                  borderRadius: BorderRadius.circular(16), // Exact Figma: rx="16"
                                  boxShadow: [
                                    BoxShadow(
                                      color: Colors.black.withOpacity(0.25), // Exact Figma: rgba(0, 0, 0, 0.25)
                                      blurRadius: 4, // Exact Figma: 4px blur
                                      offset: Offset(0, 4), // Exact Figma: 0 4px offset
                                      spreadRadius: 0,
                                    ),
                                  ],
                                ),
                                child: Material(
                                  color: Colors.transparent,
                                  child: InkWell(
                                    onTap: _isLoading ? null : _onCreateAccountPressed,
                                    borderRadius: BorderRadius.circular(16),
                                    child: Container(
                                      width: 250,
                                      height: 54,
                                      child: Center(
                                        child: _isLoading
                                            ? SizedBox(
                                                width: 20,
                                                height: 20,
                                                child: CircularProgressIndicator(
                                                  strokeWidth: 2.5,
                                                  valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                                                ),
                                              )
                                            : Text(
                                                'Create Account',
                                                style: TextStyle(
                                                  fontFamily: 'PP NeueBit',
                                                  fontSize: 16,
                                                  fontWeight: FontWeight.w700,
                                                  color: Colors.white,
                                                  letterSpacing: 0.2,
                                                ),
                                              ),
                                      ),
                                    ),
                                  ),
                                ),
                              ),
                            );
                          },
                        ),
                      ),

                      // "Have an account? Log in" link - exact Figma positioning and styling
                      Positioned(
                        left: 98.56, // Exact Figma positioning
                        top: 441.04, // Exact Figma positioning
                        child: GestureDetector(
                          onTap: _onLogInPressed,
                          child: MouseRegion(
                            cursor: SystemMouseCursors.click,
                            child: Container(
                              width: 137.211, // Exact Figma width from SVG
                              height: 12.318, // Exact Figma height from SVG
                              child: RichText(
                                text: TextSpan(
                                  children: [
                                    TextSpan(
                                      text: 'Have an account? ',
                                      style: TextStyle(
                                        fontFamily: 'PP Mondwest',
                                        fontSize: 12.318, // Exact Figma size
                                        fontWeight: FontWeight.w400,
                                        color: Color(0xFF2B2828), // Exact Figma color
                                      ),
                                    ),
                                    TextSpan(
                                      text: 'Log in',
                                      style: TextStyle(
                                        fontFamily: 'PP Mondwest',
                                        fontSize: 12.318, // Exact Figma size
                                        fontWeight: FontWeight.w400,
                                        color: Color(0xFF91B871), // Exact Figma green color for "Log in"
                                        decoration: TextDecoration.underline,
                                        decorationColor: Color(0xFF91B871),
                                        decorationThickness: 1.0,
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                            ),
                          ),
                        ),
                      ),
                    ],
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

