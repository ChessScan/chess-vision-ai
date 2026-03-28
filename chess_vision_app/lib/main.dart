import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'screens/home_screen.dart';
import 'screens/recording_screen.dart';
import 'screens/analysis_screen.dart';
import 'services/storage_service.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const ChessVisionApp());
}

class ChessVisionApp extends StatelessWidget {
  const ChessVisionApp({super.key});

  @override
  Widget build(BuildContext context) {
    return Provider<StorageService>(
      create: (_) => StorageService(),
      child: MaterialApp(
        title: 'Chess Vision',
        debugShowCheckedModeBanner: false,
        theme: ThemeData(
          colorScheme: ColorScheme.fromSeed(
            seedColor: Colors.deepPurple,
            brightness: Brightness.dark,
          ),
          useMaterial3: true,
          cardTheme: CardTheme(
            elevation: 4,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(12),
            ),
          ),
          appBarTheme: const AppBarTheme(
            centerTitle: true,
            elevation: 0,
          ),
        ),
        initialRoute: '/',
        routes: {
          '/': (context) => const HomeScreen(),
          '/record': (context) => const RecordingScreen(),
        },
        onGenerateRoute: (settings) {
          if (settings.name == '/analysis') {
            final args = settings.arguments as Map<String, dynamic>?;
            return MaterialPageRoute(
              builder: (context) => AnalysisScreen(
                recordingPath: args?['recordingPath'] ?? '',
              ),
            );
          }
          return null;
        },
      ),
    );
  }
}
