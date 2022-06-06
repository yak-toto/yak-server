<template>
  <GroupNavbar />
  <hr>
  <div class="column is-8 is-offset-2">
    <h3 class="title">Classement</h3>
    <div class="box">
      <div class="table-container">
        <table class="table is-fullwidth is-striped">
          <thead>
            <tr>
              <th>Joueur</th>
              <th>Points</th>
            </tr>
          </thead>
          <tr v-for="res in score_board_resource">
            <td>
              <div>{{ res[0] }}</div>
            </td>
            <td>
              <div>{{ res[1] }}</div>
            </td>
          </tr>
        </table>
      </div>
    </div>
  </div>
</template>

<script>
import GroupNavbar from './GroupNavbar.vue';

export default {
  name: 'ScoreBoardComponent',
  components: {
    GroupNavbar,
  },
  data() {
    return {
      score_board_resource: [],
    };
  },
  methods: {
    getScoreBoard() {
      this.$store.dispatch('getScoreBoard')
        .then((res) => { this.score_board_resource = res.data })
    },
  },
  created() {
    this.getScoreBoard()
  }
};

</script>
