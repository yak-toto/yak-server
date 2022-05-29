<template>
  <a v-on:click="getScoreBoard" class="navbar-item">Classement</a>
</template>

<script>
export default {
  name: 'ScoreBoardButton',
  methods: {
    getScoreBoard() {
      this.$router.push('/score_board');
    },
  },
};
</script>
