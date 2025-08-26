import 'package:flutter/material.dart';

// Gentle Fade Transition Route - applies to all screens except chat interface
class GentleFadeRoute extends PageRouteBuilder {
  final WidgetBuilder builder;

  GentleFadeRoute({required this.builder})
      : super(
          pageBuilder: (context, animation, secondaryAnimation) => builder(context),
          transitionDuration: const Duration(milliseconds: 1000),
          reverseTransitionDuration: const Duration(milliseconds: 1000),
          transitionsBuilder: (context, animation, secondaryAnimation, child) {
            // Create the gentle easing curve as specified in Figma
            const curve = Curves.easeOutCubic; // Gentle curve for smooth, natural feel
            final curvedAnimation = CurvedAnimation(
              parent: animation,
              curve: curve,
            );

            // Outgoing screen: fade + slight scale down
            final outgoingScale = Tween<double>(
              begin: 1.0,
              end: 0.97, // Gentle scale down for receding effect
            ).animate(curvedAnimation);

            // Incoming screen: fade + slight scale up
            final incomingScale = Tween<double>(
              begin: 1.03, // Start slightly larger for focus effect
              end: 1.0,
            ).animate(curvedAnimation);

            return Stack(
              children: [
                // Outgoing screen (current screen) - fades out while scaling down
                FadeTransition(
                  opacity: Tween<double>(
                    begin: 1.0,
                    end: 0.0,
                  ).animate(curvedAnimation),
                  child: ScaleTransition(
                    scale: outgoingScale,
                    child: Container(
                      color: Colors.white, // Background color
                      child: const Center(
                        child: CircularProgressIndicator(),
                      ),
                    ),
                  ),
                ),
                
                // Incoming screen (new screen) - fades in while scaling up
                FadeTransition(
                  opacity: curvedAnimation, // This ensures fade in from 0 to 1
                  child: ScaleTransition(
                    scale: incomingScale,
                    child: child,
                  ),
                ),
              ],
            );
          },
        );
}

// Faster version for sign up transitions (700ms)
class FastGentleFadeRoute extends PageRouteBuilder {
  final WidgetBuilder builder;

  FastGentleFadeRoute({required this.builder})
      : super(
          pageBuilder: (context, animation, secondaryAnimation) => builder(context),
          transitionDuration: const Duration(milliseconds: 700),
          reverseTransitionDuration: const Duration(milliseconds: 700),
          transitionsBuilder: (context, animation, secondaryAnimation, child) {
            // Create the gentle easing curve for faster transitions
            const curve = Curves.easeOutCubic;
            final curvedAnimation = CurvedAnimation(
              parent: animation,
              curve: curve,
            );

            // Outgoing screen: fade + slight scale down
            final outgoingScale = Tween<double>(
              begin: 1.0,
              end: 0.97,
            ).animate(curvedAnimation);

            // Incoming screen: fade + slight scale up
            final incomingScale = Tween<double>(
              begin: 1.03,
              end: 1.0,
            ).animate(curvedAnimation);

            return Stack(
              children: [
                // Outgoing screen (current screen) - fades out while scaling down
                FadeTransition(
                  opacity: Tween<double>(
                    begin: 1.0,
                    end: 0.0,
                  ).animate(curvedAnimation),
                  child: ScaleTransition(
                    scale: outgoingScale,
                    child: Container(
                      color: Colors.white,
                      child: const Center(
                        child: CircularProgressIndicator(),
                      ),
                    ),
                  ),
                ),
                
                // Incoming screen (new screen) - fades in while scaling up
                FadeTransition(
                  opacity: curvedAnimation, // This ensures fade in from 0 to 1
                  child: ScaleTransition(
                    scale: incomingScale,
                    child: child,
                  ),
                ),
              ],
            );
          },
        );
}

// Exact Figma interaction specifications route
class FigmaInteractionRoute extends PageRouteBuilder {
  final WidgetBuilder builder;

  FigmaInteractionRoute({required this.builder})
      : super(
          pageBuilder: (context, animation, secondaryAnimation) => builder(context),
          transitionDuration: const Duration(milliseconds: 900), // Balanced transition
          reverseTransitionDuration: const Duration(milliseconds: 900),
          transitionsBuilder: (context, animation, secondaryAnimation, child) {
            // Figma: "Gentle" curve - using easeOutCubic for smooth, natural feel
            const curve = Curves.easeOutCubic;
            final curvedAnimation = CurvedAnimation(
              parent: animation,
              curve: curve,
            );

            // Figma: "Smart animate" - coordinated fade + scale transitions
            // Outgoing screen: fade out + scale down
            final outgoingScale = Tween<double>(
              begin: 1.0,
              end: 0.97,
            ).animate(curvedAnimation);

            // Incoming screen: fade in + scale up
            final incomingScale = Tween<double>(
              begin: 1.03,
              end: 1.0,
            ).animate(curvedAnimation);

            return Stack(
              children: [
                // Outgoing screen (onboarding) - fades out while scaling down
                FadeTransition(
                  opacity: Tween<double>(
                    begin: 1.0,
                    end: 0.0,
                  ).animate(curvedAnimation),
                  child: ScaleTransition(
                    scale: outgoingScale,
                    child: Container(
                      color: Colors.white,
                      child: const Center(
                        child: CircularProgressIndicator(),
                      ),
                    ),
                  ),
                ),
                
                // Incoming screen (create account) - fades in while scaling up
                FadeTransition(
                  opacity: curvedAnimation, // Fade in from 0 to 1
                  child: ScaleTransition(
                    scale: incomingScale,
                    child: child,
                  ),
                ),
              ],
            );
          },
        );
}

// Global page transitions builder for MaterialApp theme
class FigmaInteractionPageTransitionsBuilder extends PageTransitionsBuilder {
  @override
  Widget buildTransitions<T extends Object?>(
    PageRoute<T> route,
    BuildContext context,
    Animation<double> animation,
    Animation<double> secondaryAnimation,
    Widget child,
  ) {
    // Create the gentle easing curve for consistent transitions
    const curve = Curves.easeOutCubic;
    final curvedAnimation = CurvedAnimation(
      parent: animation,
      curve: curve,
    );

    // Outgoing screen: fade out + scale down
    final outgoingScale = Tween<double>(
      begin: 1.0,
      end: 0.97,
    ).animate(curvedAnimation);

    // Incoming screen: fade in + scale up
    final incomingScale = Tween<double>(
      begin: 1.03,
      end: 1.0,
    ).animate(curvedAnimation);

    return Stack(
      children: [
        // Outgoing screen - fades out while scaling down
        FadeTransition(
          opacity: Tween<double>(
            begin: 1.0,
            end: 0.0,
          ).animate(curvedAnimation),
          child: ScaleTransition(
            scale: outgoingScale,
            child: Container(
              color: Colors.white,
              child: const Center(
                child: CircularProgressIndicator(),
              ),
            ),
          ),
        ),
        
        // Incoming screen - fades in while scaling up
        FadeTransition(
          opacity: curvedAnimation, // Fade in from 0 to 1
          child: ScaleTransition(
            scale: incomingScale,
            child: child,
          ),
        ),
      ],
    );
  }
}
