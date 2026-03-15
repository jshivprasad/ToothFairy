import React from 'react';
import { Redirect } from 'expo-router';
import { useAuth } from '../src/auth';
import { View, ActivityIndicator, StyleSheet } from 'react-native';
import { colors } from '../src/theme';

export default function Index() {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return (
      <View style={styles.loading}>
        <ActivityIndicator size="large" color={colors.light.primary} />
      </View>
    );
  }

  if (user) {
    return <Redirect href="/(tabs)" />;
  }

  return <Redirect href="/(auth)/login" />;
}

const styles = StyleSheet.create({
  loading: { flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: colors.light.background },
});
