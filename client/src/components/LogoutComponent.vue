<template>
  <div></div>
</template>

<script>
import axios from 'axios';

export default {
  name: 'LogoutComponent',
  created() {
    const path = 'http://localhost:5000/logout';

    axios.get(path).then((res) => this.$router.push('/'));
  },
};
</script>
