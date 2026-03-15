import { Stack } from 'expo-router';
import { AuthProvider } from '../src/auth';
import { StatusBar } from 'expo-status-bar';

export default function RootLayout() {
  return (
    <AuthProvider>
      <StatusBar style="dark" />
      <Stack screenOptions={{ headerShown: false }}>
        <Stack.Screen name="(auth)" />
        <Stack.Screen name="(tabs)" />
        <Stack.Screen name="clinic-hours" options={{ headerShown: true, title: 'Clinic Hours', headerTintColor: '#0F766E' }} />
        <Stack.Screen name="add-appointment" options={{ headerShown: true, title: 'New Appointment', headerTintColor: '#0F766E' }} />
        <Stack.Screen name="appointment-detail" options={{ headerShown: true, title: 'Appointment', headerTintColor: '#0F766E' }} />
        <Stack.Screen name="patients" options={{ headerShown: true, title: 'Patients', headerTintColor: '#0F766E' }} />
        <Stack.Screen name="ai-config" options={{ headerShown: true, title: 'AI Agent Settings', headerTintColor: '#0F766E' }} />
        <Stack.Screen name="simulate-chat" options={{ headerShown: true, title: 'Test AI Agent Call', headerTintColor: '#0F766E' }} />
        <Stack.Screen name="calendar" options={{ headerShown: true, title: 'Appointment Calendar', headerTintColor: '#0F766E' }} />
      </Stack>
    </AuthProvider>
  );
}
